import csv
import argparse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import fontManager

# --- 自動設定中文字型 ---
def set_chinese_font():
    """
    自動尋找並設定可用的中文字型（並支援 Emoji）。
    會建立一個字型列表，讓 Matplotlib 可以依序選用。
    """
    # 調整字型順序，優先使用中文字型，並將 Emoji 字型作為備援。
    font_preferences = [
        'Microsoft JhengHei',    # Windows 預設繁中
        'PingFang TC',           # macOS 預設繁中
        'Noto Sans CJK TC',      # Google 免費字型
        'Segoe UI Emoji',       # Windows Emoji 備援
    ]
    
    available_fonts = []
    for font_name in font_preferences:
        # 檢查字型是否存在於系統中
        if any(font.name == font_name for font in fontManager.ttflist):
            available_fonts.append(font_name)

    if available_fonts:
        # 設定字型列表
        plt.rcParams['font.sans-serif'] = available_fonts
        plt.rcParams['axes.unicode_minus'] = False
        print(f"成功設定字型 (依優先順序): {', '.join(available_fonts)}")
    else:
        print("警告: 未找到任何建議的中文字型或 Emoji 字型，圖表中的特殊字元可能無法正確顯示。")

def load_glucose_data(filepath, target_date_str):
    """
    從指定的路徑載入 CSV，並只篩選出指定日期的資料。
    """
    data = []
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            header = next(reader)

            for row in reader:
                if len(row) < len(header):
                    continue
                try:
                    timestamp = datetime.strptime(row[2], '%Y-%m-%d %H:%M')
                    if timestamp.date() != target_date:
                        continue # 如果日期不符，就跳過此筆紀錄

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
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 '{filepath}'")
    except Exception as e:
        print(f"讀取檔案時發生錯誤: {e}")
    
    # 依時間戳記排序，確保繪圖時順序正確
    data.sort(key=lambda r: r['timestamp'])
    return data

def plot_glucose_curve(data, date_str):
    """
    繪製血糖曲線圖。
    """
    # ... (函式其餘內容不變，除了標題設定)
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

    ax.set_ylim(0, 350)
    y_ticks = [0] + list(range(70, 181, 10)) + [350]
    ax.set_yticks(y_ticks)
    ax.set_ylabel('葡萄糖 mg/dL')

    start_day = timestamps[0].replace(hour=0, minute=0, second=0)
    end_day = start_day + timedelta(days=1)
    ax.set_xlim(start_day, end_day)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    formatted_date = date_str.replace('-', '/')
    ax.set_title(f'{formatted_date} 血糖記錄', fontsize=16)
    ax.grid(axis='x', linestyle='--', color='gray', alpha=0.5)
    
    notes_data = [r for r in data if r['record_type'] == 6 and r['notes']]
    if notes_data:
        all_glucose_values = [g for g in glucose if g is not None]
        scan_glucose_values = [r['scan_glucose'] for r in scan_data if r['scan_glucose'] is not None]
        combined_values = all_glucose_values + scan_glucose_values
        avg_glucose = sum(combined_values) / len(combined_values) if combined_values else 0
        notes_data.sort(key=lambda x: x['timestamp'])

        bottom_lanes_y = [-60, -80, -100]
        top_lanes_y = [20, 42, 64]
        
        bottom_lanes_endtime = {i: None for i in range(len(bottom_lanes_y))}
        top_lanes_endtime = {i: None for i in range(len(top_lanes_y))}

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
            lanes_y = bottom_lanes_y if is_bottom else top_lanes_y
            lanes_endtime = bottom_lanes_endtime if is_bottom else top_lanes_endtime
            
            note_width_seconds = len(note['notes']) * 720 + 600
            chosen_lane = -1
            for i in range(len(lanes_y)):
                if lanes_endtime[i] is None or note['timestamp'] > lanes_endtime[i]:
                    chosen_lane = i
                    break
            if chosen_lane == -1:
                chosen_lane = len(lanes_y) - 1
            lanes_endtime[chosen_lane] = note['timestamp'] + timedelta(seconds=note_width_seconds)
            
            y_pos = lanes_y[chosen_lane]
            anchor_y = 0 if is_bottom else 200
            va = 'top' if is_bottom else 'bottom'

            ax.annotate(note['notes'],
                        xy=(note['timestamp'], anchor_y), xycoords='data',
                        xytext=(0, y_pos), textcoords='offset points',
                        ha='left', va=va, fontsize=9,
                        arrowprops=dict(arrowstyle="->", color='gray', shrinkB=5, relpos=(0.0, 1.0) if is_bottom else (0.0, 0.0)),
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.5, alpha=0.9))

    fig.tight_layout(pad=1.5)
    plt.subplots_adjust(bottom=0.25, top=0.85)
    plt.show()

if __name__ == '__main__':
    # 設定命令列參數解析
    parser = argparse.ArgumentParser(description='從 LibreView CSV 檔案產生血糖統計圖。')
    parser.add_argument('-f', '--file', required=True, help='輸入的 CSV 資料檔案路徑。')
    parser.add_argument('-d', '--date', required=True, help='要統計的日期，格式為 YYYY-MM-DD。')
    args = parser.parse_args()

    set_chinese_font()
    
    # 載入指定日期的資料
    glucose_records = load_glucose_data(args.file, args.date)

    # 如果有找到資料，才繪製圖表
    if glucose_records:
        plot_glucose_curve(glucose_records, args.date)
    else:
        print(f"在檔案 '{args.file}' 中找不到日期為 '{args.date}' 的任何資料。")