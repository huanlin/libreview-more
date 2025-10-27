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

    fig, ax = plt.subplots(figsize=(17, 8))
    
    ax.axhspan(70, 180, color='gray', alpha=0.2)
    ax.plot(timestamps, glucose, marker='o', linestyle='-', color='#1f77b4', markersize=4, zorder=4)
    
    scan_data = [r for r in data if r['record_type'] == 1 and r['scan_glucose']]
    if scan_data:
        scan_ts = [r['timestamp'] for r in scan_data]
        scan_val = [r['scan_glucose'] for r in scan_data]
        ax.scatter(scan_ts, scan_val, c='orange', s=20, zorder=5)

    all_glucose_data = historic_data + scan_data
    
    # --- 標註每兩小時內的最高點與最低點 ---
    start_day_for_intervals = timestamps[0].replace(hour=0, minute=0, second=0)
    annotated_points = set()

    for i in range(12):
        interval_start = start_day_for_intervals + timedelta(hours=i*2)
        interval_end = start_day_for_intervals + timedelta(hours=(i+1)*2)
        
        points_in_interval = [p for p in all_glucose_data if interval_start <= p['timestamp'] < interval_end]
        
        if not points_in_interval:
            continue
            
        get_glucose = lambda p: p.get('historic_glucose') or p.get('scan_glucose')
        max_point = max(points_in_interval, key=get_glucose)
        min_point = min(points_in_interval, key=get_glucose)
        
        max_val = get_glucose(max_point)
        max_point_id = (max_point['timestamp'], max_val)
        if max_point_id not in annotated_points:
            ax.annotate(max_val, (max_point['timestamp'], max_val), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)
            annotated_points.add(max_point_id)

        min_val = get_glucose(min_point)
        min_point_id = (min_point['timestamp'], min_val)
        if min_point_id not in annotated_points and min_point_id != max_point_id:
            ax.annotate(min_val, (min_point['timestamp'], min_val), textcoords="offset points", xytext=(0, -20), ha='center', fontsize=9)
            annotated_points.add(min_point_id)

    ax.set_ylim(0, 450)
    ax.set_yticks([0, 70, 180, 350])
    ax.set_ylabel('葡萄糖 mg/dL')

    start_day = timestamps[0].replace(hour=0, minute=0, second=0)
    end_day = start_day + timedelta(days=1)
    ax.set_xlim(start_day, end_day)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    ax.set_title('每日血糖模式', fontsize=16)
    ax.grid(axis='x', linestyle='--', color='gray', alpha=0.5)
    
    # --- 繪製備註 (依據血糖高低，上下動態排列) ---
    notes_data = [r for r in data if r['record_type'] == 6 and r['notes']]
    if notes_data:
        all_glucose_values = [g for g in glucose if g is not None]
        scan_glucose_values = [r['scan_glucose'] for r in scan_data if r['scan_glucose'] is not None]
        combined_values = all_glucose_values + scan_glucose_values
        avg_glucose = sum(combined_values) / len(combined_values) if combined_values else 0

        notes_data.sort(key=lambda x: x['timestamp'])

        bottom_y_levels = [-60, -100, -140]
        top_y_levels = [220, 265, 310]
        
        last_note_info_bottom = None
        last_note_info_top = None

        for note in notes_data:
            cur_glucose = None
            for p in all_glucose_data:
                if p['timestamp'] == note['timestamp']:
                    cur_glucose = p.get('historic_glucose') or p.get('scan_glucose')
                    break
            if cur_glucose is None:
                closest_point = min([p for p in all_glucose_data if p['timestamp'] < note['timestamp']], key=lambda x: note['timestamp'] - x['timestamp'], default=None)
                if closest_point:
                    cur_glucose = closest_point.get('historic_glucose') or closest_point.get('scan_glucose')
            if cur_glucose is None:
                cur_glucose = avg_glucose

            is_bottom = cur_glucose < avg_glucose

            if is_bottom:
                levels = bottom_y_levels
                last_info = last_note_info_bottom
                anchor_y = 0
                va = 'top'
            else:
                levels = top_y_levels
                last_info = last_note_info_top
                anchor_y = 200
                va = 'bottom'

            chosen_level_index = 0
            if last_info:
                last_ts, last_len, last_level_index = last_info
                required_seconds = (last_len / 2 + len(note['notes']) / 2) * 720
                actual_seconds = (note['timestamp'] - last_ts).total_seconds()
                if actual_seconds < required_seconds:
                    chosen_level_index = min(last_level_index + 1, len(levels) - 1)
            
            y_pos = levels[chosen_level_index]

            if is_bottom:
                # --- 下方備註：relpos=(0,1) 表示箭頭從文字框的「左上角」出發 ---
                ax.annotate(note['notes'],
                            xy=(note['timestamp'], anchor_y), xycoords='data',
                            xytext=(0, y_pos), textcoords='offset points',
                            ha='left', va='top', fontsize=9,
                            arrowprops=dict(arrowstyle="->", color='gray', shrinkB=5, relpos=(0.0, 1.0)),
                            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.5, alpha=0.9))
            else:
                # --- 上方備註：relpos=(0,0) 表示箭頭從文字框的「左下角」出發 ---
                ax.annotate(note['notes'],
                            xy=(note['timestamp'], anchor_y), xycoords='data',
                            xytext=(note['timestamp'], y_pos), textcoords='data',
                            ha='left', va='bottom', fontsize=9,
                            arrowprops=dict(arrowstyle="->", color='gray', shrinkA=5, relpos=(0.0, 0.0)),
                            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.5, alpha=0.9))

            if is_bottom:
                last_note_info_bottom = (note['timestamp'], len(note['notes']), chosen_level_index)
            else:
                last_note_info_top = (note['timestamp'], len(note['notes']), chosen_level_index)

    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    csv_filepath = 'requirement/sample-glucose_2025-10-27.csv'
    glucose_records = load_glucose_data(csv_filepath)
    plot_glucose_curve(glucose_records)
