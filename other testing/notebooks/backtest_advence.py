import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# ⚙️ ตั้งค่าพอร์ตโฟลิโอ (Strategy Settings)
# ==========================================
initial_capital = 1_000_000 
csv_filename = 'tradingview_data.csv'

# 1. สูตรเดิม (Aggressive Buy & Hold)
weights_original = {'FRT': 0.40, 'HPG': 0.40, 'MWG': 0.20}

# 2. สูตรใหม่มีกันชน (Buffered) - ลดสัดส่วนตัวแรง มาใส่ Defensive
weights_buffered = {'FRT': 0.35, 'HPG': 0.35, 'MWG': 0.20, 'POW': 0.10}

# ==========================================

def load_data(filename):
    # ฟังก์ชันอ่านไฟล์ CSV เหมือนเดิม
    try:
        df = pd.read_csv(filename)
        time_col = df.columns[0]
        try:
            if df[time_col].dtype in ['int64', 'float64']:
                df[time_col] = pd.to_datetime(df[time_col], unit='s')
            else:
                df[time_col] = pd.to_datetime(df[time_col])
        except: pass
        df.set_index(time_col, inplace=True)
        df.columns = [col.split(' ')[0] for col in df.columns]
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_strategy(prices, weights, rebalance=False):
    """
    Core Engine สำหรับคำนวณเงินในพอร์ต
    rebalance=True : จะทำการปรับพอร์ตทุกต้นปี (Sell High, Buy Low)
    rebalance=False: ถือยาว (Let Profit Run) สัดส่วนจะเพี้ยนไปตามราคาหุ้น
    """
    # กรองเอาเฉพาะหุ้นที่มีในสูตร
    tickers = list(weights.keys())
    data = prices[tickers].dropna()
    
    # เงินลงทุนเริ่มต้น
    cash = initial_capital
    
    # คำนวณจำนวนหุ้นที่ซื้อได้ ณ วันแรก
    shares = {}
    start_prices = data.iloc[0]
    for ticker, w in weights.items():
        shares[ticker] = (cash * w) / start_prices[ticker]
        
    equity_curve = []
    
    # วนลูปตรวจสอบทีละวัน (Time-Series Loop)
    current_year = data.index[0].year
    
    for date, row in data.iterrows():
        # 1. คำนวณมูลค่าพอร์ตวันนี้
        current_val = sum(shares[t] * row[t] for t in tickers)
        equity_curve.append(current_val)
        
        # 2. Logic การ Rebalance (ปรับพอร์ต)
        if rebalance:
            # ถ้าปีเปลี่ยน (ขึ้นปีใหม่) ให้ปรับพอร์ต
            if date.year != current_year:
                # print(f"🔄 Rebalancing at {date.date()}...") # ปลดคอมเมนต์ถ้าอยากเห็น log
                
                # คำนวณจำนวนหุ้นใหม่ ตามมูลค่าพอร์ตปัจจุบัน
                # (ขายตัวแพง ซื้อตัวถูก ให้กลับมาเท่า % เป้าหมาย)
                for ticker, w in weights.items():
                    shares[ticker] = (current_val * w) / row[ticker]
                
                current_year = date.year # อัปเดตปีปัจจุบัน

    return pd.Series(equity_curve, index=data.index)

# --- Main Execution ---
df = load_data(csv_filename)

if df is not None:
    print("✅ กำลังประมวลผล Backtest 3 รูปแบบ...")
    
    # เตรียมข้อมูลราคา
    all_tickers = list(set(list(weights_original.keys()) + list(weights_buffered.keys())))
    price_data = df[all_tickers].dropna()

    # 1. Run: Original (Buy & Hold)
    equity_orig = run_strategy(price_data, weights_original, rebalance=False)
    
    # 2. Run: Buffered (Buy & Hold)
    equity_buf = run_strategy(price_data, weights_buffered, rebalance=False)
    
    # 3. Run: Buffered + Rebalancing (พระเอกของเรา)
    equity_rebal = run_strategy(price_data, weights_buffered, rebalance=True)

    # --- คำนวณ Max Drawdown เพื่อดูความเสี่ยง ---
    def get_max_dd(equity):
        return ((equity - equity.cummax()) / equity.cummax()).min() * 100

    dd_orig = get_max_dd(equity_orig)
    dd_rebal = get_max_dd(equity_rebal)

    print(f"\n📊 ผลลัพธ์การ Backtest:")
    print(f"1. Original (40/40/20):")
    print(f"   - เงินจบ: {equity_orig.iloc[-1]:,.0f} บาท")
    print(f"   - ความเสี่ยงสูงสุด (Max DD): {dd_orig:.2f}%")
    
    print(f"\n2. New Strategy (Buffer + Rebalance):")
    print(f"   - เงินจบ: {equity_rebal.iloc[-1]:,.0f} บาท")
    print(f"   - ความเสี่ยงสูงสุด (Max DD): {dd_rebal:.2f}%")
    
    print(f"\n👉 ความต่าง: ลดความเสี่ยงได้ {abs(dd_orig - dd_rebal):.2f}%")

    # --- Plot Graph ---
    plt.figure(figsize=(12, 6))
    
    plt.plot(equity_orig, label='Original (Buy & Hold)', color='gray', linestyle='--', alpha=0.7)
    plt.plot(equity_buf, label='Buffered + POW (Buy & Hold)', color='orange', alpha=0.8)
    plt.plot(equity_rebal, label='Buffered + POW (Rebalanced Yearly)', color='green', linewidth=2.5)
    
    plt.title('Comparison: Original vs Buffered vs Rebalanced Portfolio', fontsize=14)
    plt.ylabel('Portfolio Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()