import csv
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import fontManager

# --- 自動設定中文字型 ---
def set_chinese_font():
    """
    自動尋找並設定可用的中文字型。
    """
    supported_fonts = [
        'Microsoft JhengHei',  # Windows - 微軟正黑體
        'PingFang TC',         # macOS - 蘋方-繁
        'Noto Sans CJK TC',    # Linux/Other - 思源黑體 繁中
        'Arial Unicode MS'     # 通用 Unicode 字型
    ]
    
    for font_name in supported_fonts:
        try:
            # 檢查字型是否存在
            if any(font.name == font_name for font in fontManager.ttflist):
                plt.rcParams['font.sans-serif'] = [font_name]
                plt.rcParams['axes.unicode_minus'] = False
                print(f"成功設定中文字型: {font_name}")
                return
        except Exception:
            continue
            
    print("警告: 未找到可用的中文字型。")
    print("圖表中的中文可能無法正確顯示。")
    print("請嘗試安裝以下任一字型: Microsoft JhengHei, PingFang TC, Noto Sans CJK TC")

set_chinese_font() # 執行字型設定

def load_glucose_data(filepath):
    """
    從指定的路徑載入並解析血糖數據 CSV 檔案。
    """
    data = []
    with open(filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        header = next(reader)

        for row in reader:
            if len(row) < len(header):
                continue
            try:
                timestamp = datetime.strptime(row[2], '%Y-%m-%d %H:%M')
                record = {
                    'timestamp': timestamp,
                    'record_type': int(row[3]),
                    'historic_glucose': int(row[4]) if row[4] else None,
                    'scan_glucose': int(row[5]) if row[5] else None,
                    'notes': row[13] if row[13] else None
                }
                data.append(record)
            except (ValueError, IndexError):
                pass
    return data

def plot_glucose_curve(data):
    """
    繪製血糖曲線圖。
    """
    historic_data = [r for r in data if r['record_type'] == 0 and r['historic_glucose']]
    if not historic_data:
        print("無歷史血糖數據可供繪圖。")
        return
        
    timestamps = [r['timestamp'] for r in historic_data]
    glucose = [r['historic_glucose'] for r in historic_data]

    fig, ax = plt.subplots(figsize=(17, 6))
    
    ax.axhspan(70, 180, color='gray', alpha=0.2)
    ax.plot(timestamps, glucose, marker='o', linestyle='-', color='#1f77b4', markersize=4, zorder=4)
    
    scan_data = [r for r in data if r['record_type'] == 1 and r['scan_glucose']]
    if scan_data:
        scan_ts = [r['timestamp'] for r in scan_data]
        scan_val = [r['scan_glucose'] for r in scan_data]
        ax.scatter(scan_ts, scan_val, c='orange', s=20, zorder=5)

    # --- 統一處理歷史與掃描數據，標註每兩小時內的最高點與最低點 ---
    all_glucose_data = historic_data + scan_data
    start_day_for_intervals = timestamps[0].replace(hour=0, minute=0, second=0)
    annotated_points = set()

    for i in range(12): # 將一天分為12個兩小時區間
        interval_start = start_day_for_intervals + timedelta(hours=i*2)
        interval_end = start_day_for_intervals + timedelta(hours=(i+1)*2)
        
        points_in_interval = [
            p for p in all_glucose_data 
            if interval_start <= p['timestamp'] < interval_end
        ]
        
        if not points_in_interval:
            continue
            
        # 找出區間內的最高與最低點
        # 我們需要一個統一的鍵名來取得血糖值
        get_glucose = lambda p: p.get('historic_glucose') or p.get('scan_glucose')
        max_point = max(points_in_interval, key=get_glucose)
        min_point = min(points_in_interval, key=get_glucose)
        
        # 標註最高點
        max_val = get_glucose(max_point)
        max_point_id = (max_point['timestamp'], max_val)
        if max_point_id not in annotated_points:
            ax.annotate(max_val,
                        (max_point['timestamp'], max_val),
                        textcoords="offset points", xytext=(0, 10),
                        ha='center', fontsize=9)
            annotated_points.add(max_point_id)

        # 標註最低點
        min_val = get_glucose(min_point)
        min_point_id = (min_point['timestamp'], min_val)
        if min_point_id not in annotated_points and min_point_id != max_point_id:
            ax.annotate(min_val,
                        (min_point['timestamp'], min_val),
                        textcoords="offset points", xytext=(0, -20),
                        ha='center', fontsize=9)
            annotated_points.add(min_point_id)

    ax.set_ylim(0, 350)
    ax.set_yticks([0, 70, 180, 350])
    ax.set_ylabel('葡萄糖 mg/dL')

    start_day = timestamps[0].replace(hour=0, minute=0, second=0)
    end_day = start_day + timedelta(days=1)
    ax.set_xlim(start_day, end_day)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    ax.set_title('每日血糖模式', fontsize=16)
    ax.grid(axis='x', linestyle='--', color='gray', alpha=0.5)
    
    # --- 繪製備註 ---
    notes_data = [r for r in data if r['record_type'] == 6 and r['notes']]
    if notes_data:
        note_y_positions = [-0.15, -0.25, -0.35, -0.45] # Y軸的相對位置，用來分行
        note_last_x = {} # 記錄每一行的最後一個X位置，避免重疊

        for i, note in enumerate(notes_data):
            y_pos_index = i % len(note_y_positions)
            y_pos = note_y_positions[y_pos_index]
            
            # 簡單的防重疊：如果跟同行前一個太近，就換行
            if y_pos_index in note_last_x and (note['timestamp'] - note_last_x[y_pos_index]).total_seconds() < 7200:
                 y_pos_index = (y_pos_index + 1) % len(note_y_positions)
                 y_pos = note_y_positions[y_pos_index]

            ax.annotate(note['notes'], 
                        xy=(note['timestamp'], 0), 
                        xycoords='data',
                        xytext=(0, y_pos * ax.get_ylim()[1]), 
                        textcoords='offset points',
                        ha='center', 
                        fontsize=9,
                        arrowprops=dict(arrowstyle='->', color='gray'))
            note_last_x[y_pos_index] = note['timestamp']

    fig.tight_layout()
    # 調整圖表邊距，為下方的備註留出空間
    plt.subplots_adjust(bottom=0.3)
    plt.show()

if __name__ == '__main__':
    csv_filepath = 'requirement/sample-glucose_2025-10-27.csv'
    glucose_records = load_glucose_data(csv_filepath)
    plot_glucose_curve(glucose_records)
