import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ตั้งค่าชื่อไฟล์
csv_filename = 'tradingview_data.csv'

def analyze_tradingview_data_v2(filename):
    try:
        print(f"📂 กำลังอ่านไฟล์: {filename} ...")
        df = pd.read_csv(filename)
        
        # 1. จัดการเรื่องเวลา (Index)
        time_col = df.columns[0]
        try:
            if df[time_col].dtype in ['int64', 'float64']:
                df[time_col] = pd.to_datetime(df[time_col], unit='s')
            else:
                df[time_col] = pd.to_datetime(df[time_col])
        except Exception:
            pass # ถ้าแปลงไม่ได้ ให้ใช้ค่าเดิมไปก่อน
        
        df.set_index(time_col, inplace=True)

        # 2. ทำความสะอาดชื่อ Column (เอาคำว่า ' · HOSE: close' ออก เพื่อให้อ่านง่าย)
        # ตัวอย่าง: 'HPG · HOSE: close' -> 'HPG'
        df.columns = [col.split(' ')[0] for col in df.columns]
        print(f"📊 หุ้นที่พบ: {df.columns.tolist()}")

        # 3. แปลงข้อมูลเป็นตัวเลข (Force Numeric)
        # เผื่อมี text แปลกๆ เช่น 'Invalid symbol' จะถูกเปลี่ยนเป็น NaN
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 4. ลบ Column ที่ไม่มีข้อมูลเลย (All NaN) ออกไปก่อน
        df.dropna(axis=1, how='all', inplace=True)

        # 5. คำนวณ Returns (โดยไม่ใช้ dropna แบบเหมารวม)
        # ใช้ fill_method=None เพื่อแก้ Warning ในอนาคต
        returns = df.pct_change(fill_method=None)

        # 6. คำนวณ Correlation
        # pandas.corr() จะจัดการ NaN ให้เอง (คำนวณเฉพาะช่วงที่มีข้อมูลตรงกัน)
        corr_matrix = returns.corr()

        print("\n--- Correlation Matrix Result (Top Pairs) ---")
        print(corr_matrix.round(2))

        # 7. พล็อตกราฟ
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, 
                    annot=True, 
                    cmap='coolwarm', 
                    vmin=-1, vmax=1, 
                    fmt=".2f",
                    linewidths=0.5)
        
        plt.title('Vietnam Stock Correlation Matrix (Pairwise Analysis)', fontsize=16)
        plt.tight_layout()
        plt.show()

    except FileNotFoundError:
        print(f"❌ Error: ไม่พบไฟล์ {filename}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_tradingview_data_v2(csv_filename)