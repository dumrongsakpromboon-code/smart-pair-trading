import pandas as pd
import numpy as np
import scipy.optimize as sco
import matplotlib.pyplot as plt

# ==========================================
# ⚙️ ตั้งค่า: เลือกหุ้นที่ต้องการนำมาจัดพอร์ต
# ใส่ชื่อ Ticker ตามที่ปรากฏใน CSV ของคุณ (เอาชื่อย่อหน้าแรก)
selected_tickers = ['HPG', 'MWG', 'FRT', 'POW', 'PNJ'] 

# ชื่อไฟล์ CSV
csv_filename = 'tradingview_data.csv'

# สมมติอัตราผลตอบแทนพันธบัตร (Risk-Free Rate) เพื่อใช้คำนวณ Sharpe Ratio
# ของเวียดนามอาจจะอยู่ที่ประมาณ 2-3% ต่อปี (ใส่เป็นทศนิยม)
risk_free_rate = 0.02
# ==========================================

def get_clean_data(filename, tickers):
    try:
        df = pd.read_csv(filename)
        
        # จัดการเรื่องเวลา
        time_col = df.columns[0]
        try:
            if df[time_col].dtype in ['int64', 'float64']:
                df[time_col] = pd.to_datetime(df[time_col], unit='s')
            else:
                df[time_col] = pd.to_datetime(df[time_col])
        except:
            pass
        df.set_index(time_col, inplace=True)

        # Clean ชื่อ Column
        df.columns = [col.split(' ')[0] for col in df.columns]
        
        # เลือกเฉพาะหุ้นที่เราสนใจ
        data = df[tickers].copy()
        
        # แปลงเป็นตัวเลขและลบ NaN
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # ใช้ data.dropna() เพื่อให้ได้ช่วงเวลาที่ทุกตัวมีข้อมูลพร้อมกันจริงๆ
        # (สำคัญมากสำหรับการทำ Optimization เพื่อความยุติธรรม)
        data.dropna(inplace=True)
        
        return data
    except KeyError as e:
        print(f"❌ Error: ไม่พบชื่อหุ้น {e} ในไฟล์ CSV โปรดเช็คชื่อ Ticker อีกครั้ง")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error: {e}")
        return pd.DataFrame()

# ฟังก์ชันคำนวณสถิติพอร์ต
def portfolio_performance(weights, mean_returns, cov_matrix):
    returns = np.sum(mean_returns * weights) * 252 # 252 วันทำการต่อปี
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return returns, std

# ฟังก์ชันติดลบ Sharpe Ratio (เพื่อใช้กับ Minimize Function)
def neg_sharpe_ratio(weights, mean_returns, cov_matrix, rf_rate):
    p_ret, p_std = portfolio_performance(weights, mean_returns, cov_matrix)
    return - (p_ret - rf_rate) / p_std

# --- Main Script ---
data = get_clean_data(csv_filename, selected_tickers)

if not data.empty:
    print(f"✅ ดึงข้อมูลสำเร็จ: {len(data)} วันทำการ")
    print(f"💼 หุ้นในพอร์ต: {selected_tickers}")
    
    # 1. คำนวณ Returns รายวัน
    returns = data.pct_change(fill_method=None).dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    # 2. ตั้งค่า Optimization
    num_assets = len(selected_tickers)
    args = (mean_returns, cov_matrix, risk_free_rate)
    
    # ข้อจำกัด: น้ำหนักรวมกันต้องเท่ากับ 1 (100%)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    # ขอบเขต: หุ้นแต่ละตัวถือได้ตั้งแต่ 0% ถึง 100% (No Short Selling)
    bounds = tuple((0.0, 1.0) for asset in range(num_assets))
    
    # เริ่มต้นสุ่มน้ำหนักเท่าๆ กัน
    init_guess = num_assets * [1. / num_assets,]

    # 3. รัน Optimization (หาค่า Sharpe สูงสุด)
    result = sco.minimize(neg_sharpe_ratio, init_guess, args=args,
                          method='SLSQP', bounds=bounds, constraints=constraints)

    # 4. แสดงผลลัพธ์
    print("\n" + "="*40)
    print("🏆 PORTFOLIO OPTIMIZATION RESULT")
    print("="*40)
    
    optimal_weights = result.x
    
    print("\n📊 สัดส่วนที่แนะนำ (Optimal Weights):")
    for ticker, weight in zip(selected_tickers, optimal_weights):
        print(f"  • {ticker:<5}: {weight*100:.2f}%")

    # คำนวณ Performance ของพอร์ตเทพ
    opt_ret, opt_vol = portfolio_performance(optimal_weights, mean_returns, cov_matrix)
    opt_sharpe = (opt_ret - risk_free_rate) / opt_vol

    print("\n📈 คาดการณ์ผลตอบแทน (Annualized):")
    print(f"  • Return:      {opt_ret*100:.2f}% ต่อปี")
    print(f"  • Volatility:  {opt_vol*100:.2f}% (ความผันผวน)")
    print(f"  • Sharpe Ratio: {opt_sharpe:.2f} (ยิ่งสูงยิ่งดี)")
    print("="*40)

    # 5. (Optional) พล็อตกราฟ Pie Chart
    plt.figure(figsize=(7, 7))
    # กรองตัวที่น้ำหนักน้อยมากๆ ออก (เช่น < 1%) เพื่อความสวยงาม
    labels = []
    sizes = []
    for t, w in zip(selected_tickers, optimal_weights):
        if w > 0.01: # แสดงเฉพาะตัวที่มีนัยสำคัญ (>1%)
            labels.append(t)
            sizes.append(w)
            
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    plt.title('Optimal Portfolio Allocation (Max Sharpe)')
    plt.show()

else:
    print("⚠️ ไม่สามารถคำนวณได้เนื่องจากข้อมูลไม่เพียงพอ")