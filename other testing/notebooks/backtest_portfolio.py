import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# ⚙️ ตั้งค่าพอร์ตโฟลิโอของคุณ
# ใส่สัดส่วนน้ำหนักตามที่คำนวณได้ (รวมกันควรได้ 1.0 หรือใกล้เคียง)
weights = {
    'FRT': 0.40,  # 40%
    'HPG': 0.40,  # 40%
    'MWG': 0.20,  # 20%
    # 'POW': 0.0, # ถ้ามีตัวอื่นใส่เพิ่มได้
}

# เงินตั้งต้น (สมมติ 1 ล้าน)
initial_capital = 1_000_000 

# ชื่อไฟล์ CSV
csv_filename = 'tradingview_data.csv'
# ==========================================

def run_backtest(filename, weights, capital):
    try:
        # 1. อ่านและ Clean ข้อมูล (ใช้ Logic เดิมที่เสถียรแล้ว)
        df = pd.read_csv(filename)
        time_col = df.columns[0]
        try:
            if df[time_col].dtype in ['int64', 'float64']:
                df[time_col] = pd.to_datetime(df[time_col], unit='s')
            else:
                df[time_col] = pd.to_datetime(df[time_col])
        except: pass
        df.set_index(time_col, inplace=True)
        
        # Clean ชื่อ Column
        original_columns = df.columns.tolist()
        df.columns = [col.split(' ')[0] for col in df.columns]
        
        # แปลงเป็นตัวเลข
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # หุ้นในพอร์ต
        tickers = list(weights.keys())
        
        # 2. แยกข้อมูล Benchmark (VNINDEX) และ หุ้นในพอร์ต
        # สมมติว่า Column แรกสุดคือ Benchmark (ใน TradingView Export มักเป็นแบบนั้น)
        benchmark_col = df.columns[0] 
        benchmark_data = df[[benchmark_col]].copy().dropna()
        
        # ดึงข้อมูลหุ้นในพอร์ต
        portfolio_data = df[tickers].copy().dropna()
        
        # *สำคัญ* เพื่อการเปรียบเทียบที่ยุติธรรม เราจะตัดข้อมูลให้เหลือเฉพาะช่วงวันที่ "มีข้อมูลครบทุกตัว"
        # (Intersection of dates)
        common_dates = portfolio_data.index.intersection(benchmark_data.index)
        portfolio_data = portfolio_data.loc[common_dates]
        benchmark_data = benchmark_data.loc[common_dates]
        
        print(f"✅ ช่วงเวลา Backtest: {common_dates.min().date()} ถึง {common_dates.max().date()}")
        print(f"📊 จำนวนวันทำการ: {len(common_dates)} วัน")

        # 3. คำนวณ Returns
        # Daily Return ของหุ้นรายตัว
        stock_returns = portfolio_data.pct_change().fillna(0)
        
        # Daily Return ของ Benchmark
        benchmark_returns = benchmark_data.pct_change().fillna(0)
        
        # 4. คำนวณ Portfolio Return (Weighted Sum)
        # สูตร: ผลตอบแทนพอร์ต = (Return A * Weight A) + (Return B * Weight B) ...
        portfolio_daily_ret = stock_returns.dot(pd.Series(weights))
        
        # 5. สร้าง Equity Curve (กราฟเงินเติบโต)
        # สูตร: เงินต้น * (1 + daily_return).cumprod()
        portfolio_equity = capital * (1 + portfolio_daily_ret).cumprod()
        benchmark_equity = capital * (1 + benchmark_returns[benchmark_col]).cumprod()
        
        # 6. คำนวณ Key Metrics (KPIs)
        total_return_port = (portfolio_equity.iloc[-1] / capital) - 1
        total_return_bench = (benchmark_equity.iloc[-1] / capital) - 1
        
        # Max Drawdown (จุดขาดทุนสูงสุดจากยอดดอย)
        rolling_max = portfolio_equity.cummax()
        drawdown = (portfolio_equity - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        print("\n" + "="*40)
        print("🚀 BACKTEST RESULTS")
        print("="*40)
        print(f"💰 เงินเริ่มต้น:      {capital:,.2f}")
        print(f"🏁 เงินสุดท้าย (Port): {portfolio_equity.iloc[-1]:,.2f} (+{total_return_port*100:.2f}%)")
        print(f"🏢 เงินสุดท้าย (Index):{benchmark_equity.iloc[-1]:,.2f} (+{total_return_bench*100:.2f}%)")
        print("-" * 40)
        if total_return_port > total_return_bench:
            print(f"🏆 พอร์ตนี้ 'ชนะ' ตลาดอยู่: +{(total_return_port - total_return_bench)*100:.2f}%")
        else:
            print(f"📉 พอร์ตนี้ 'แพ้' ตลาดอยู่: {(total_return_port - total_return_bench)*100:.2f}%")
        
        print(f"⚠️ Max Drawdown: {max_drawdown*100:.2f}% (จุดลึกสุดที่พอร์ตเคยติดลบจากยอด)")

        # 7. พล็อตกราฟ
        plt.figure(figsize=(12, 6))
        
        # เส้น Equity Curve
        plt.plot(portfolio_equity, label='My Optimized Portfolio', linewidth=2, color='green')
        plt.plot(benchmark_equity, label='VNINDEX (Benchmark)', linewidth=2, color='gray', linestyle='--')
        
        plt.title('Backtest: Optimized Portfolio (40/40/20) vs VNINDEX', fontsize=14)
        plt.ylabel('Portfolio Value (Currency)')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        
        # Fill พื้นที่แสดง Drawdown (ทางเลือก)
        plt.fill_between(portfolio_equity.index, portfolio_equity, benchmark_equity, 
                         where=(portfolio_equity > benchmark_equity), 
                         interpolate=True, color='green', alpha=0.1)
        
        plt.tight_layout()
        plt.show()

    except KeyError as e:
        print(f"❌ Error: ไม่พบชื่อหุ้น {e} ตรวจสอบตัวสะกดใน CSV หรือตัวแปร weights")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_backtest(csv_filename, weights, initial_capital)