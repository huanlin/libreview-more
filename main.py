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
    with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as csvfile:
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
        ax.scatter(scan_ts, scan_val, c='orange', s=60, zorder=5)
        for i, txt in enumerate(scan_val):
            ax.annotate(txt, (scan_ts[i], scan_val[i]), textcoords="offset points", xytext=(0,8), ha='center', fontsize=9)

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
    
    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    csv_filepath = 'requirement/sample-glucose_2025-10-27.csv'
    glucose_records = load_glucose_data(csv_filepath)
    plot_glucose_curve(glucose_records)
