import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import gspread
from datetime import datetime, timedelta
from data_processing import get_market_data
from strategy import calculate_portfolio_values, calculate_target_values, calculate_target_diffs, get_z_score_advice, generate_action_card

# ---------------------------------------------------------
# ⚙️ CONFIGURATION & DB CONNECTION
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Pair Trading AI", layout="wide", page_icon="📈")

# ตั้งชื่อไฟล์ Sheet ที่จะใช้เก็บข้อมูล (ต้องตรงกับที่คุณสร้างไว้)
SHEET_NAME = "Smart_Portfolio_ZScore_Edition"
CREDENTIALS_FILE = 'client_secret.json'

# ฟังก์ชันเชื่อมต่อ Database (Google Sheet)
@st.cache_resource
def init_connection():
    # Returns a tuple: (connection_object, status_message, error_message, warning_message)
    warning_message = None
    try:
        # 1. ลองเชื่อมต่อผ่าน Streamlit Secrets (สำหรับ Cloud)
        if "gcp_service_account" in st.secrets:
            creds = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds:
                creds["private_key"] = creds["private_key"].replace("\\n", "\n")
            client = gspread.service_account_from_dict(creds)
            sh = client.open(SHEET_NAME)
            return sh, "☁️ Connected via Streamlit Secrets!", None, None
    except Exception as e:
        warning_message = f"🤫 Secrets connection failed. Will try local file next."
        # Don't return here, let it fall through to the next method

    # 2. ถ้าไม่มี Secrets ให้ลองหาไฟล์ Local (สำหรับเครื่องตัวเอง)
    try:
        client = gspread.oauth(
            credentials_filename=CREDENTIALS_FILE,
            authorized_user_filename='token.json'
        )
        sh = client.open(SHEET_NAME)
        return sh, "📄 Connected via local file!", None, warning_message
    except Exception as e:
        error_message = (
            "💥 **Connection Failed**\n"
            f"Could not connect to Google Sheets using any method.\n"
            f"**Details:** {e}\n"
            "Please ensure you have a valid `client_secret.json` for local use, "
            "or have configured `gcp_service_account` secrets for cloud deployment."
        )
        return None, None, error_message, warning_message

# ฟังก์ชันคำนวณยอดสินทรัพย์คงเหลือจากประวัติ
def calculate_current_holdings(trade_history_df):
    asset1_holdings = 0.0
    asset2_holdings = 0.0

    if trade_history_df.empty:
        return 0.0, 0.0

    # Use consistent internal column names
    asset1_col_name = 'asset1_action'
    asset2_col_name = 'asset2_action'

    for index, row in trade_history_df.iterrows():
        # Process Asset 1
        action1 = str(row.get(asset1_col_name, '-'))
        if ':' in action1 or ' ' in action1:
            parts = action1.replace(':', ' ').split()
            if len(parts) >= 2:
                act, amount_str = parts[0], parts[1]
                try:
                    amount = float(amount_str)
                    if act.upper() == 'BUY':
                        asset1_holdings += amount
                    elif act.upper() == 'SELL':
                        asset1_holdings -= amount
                except ValueError:
                    pass # Ignore if amount is not a valid float

        # Process Asset 2
        action2 = str(row.get(asset2_col_name, '-'))
        if ':' in action2 or ' ' in action2:
            parts = action2.replace(':', ' ').split()
            if len(parts) >= 2:
                act, amount_str = parts[0], parts[1]
                try:
                    amount = float(amount_str)
                    if act.upper() == 'BUY':
                        asset2_holdings += amount
                    elif act.upper() == 'SELL':
                        asset2_holdings -= amount
                except ValueError:
                    pass # Ignore if amount is not a valid float

    return asset1_holdings, asset2_holdings

# ฟังก์ชันดึงประวัติการเทรด
def load_trade_history(sh):
    try:
        ws = sh.worksheet("History_Log")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        # Define potential old and new column names
        column_map = {
            'Gold Action': 'asset1_action',
            'Silver Action': 'asset2_action',
            'asset1_act': 'asset1_action',
            'asset2_act': 'asset2_action'
        }
        
        # Rename columns that exist in the dataframe
        df.rename(columns={k: v for k, v in column_map.items() if k in df.columns}, inplace=True)
        
        return df
    except Exception as e:
        return pd.DataFrame()

# ฟังก์ชันบันทึกการเทรดใหม่
def save_transaction(sh, date, action_type, z_score, asset1_act, asset2_act, note):
    try:
        ws = sh.worksheet("History_Log")
        # Ensure the header row in Google Sheet is ['date', 'action_type', 'z_score', 'asset1_act', 'asset2_act', 'note']
        row = [str(date), action_type, z_score, asset1_act, asset2_act, note]
        ws.append_row(row)
        st.toast('✅ บันทึกข้อมูลสำเร็จ!', icon='💾')
        st.cache_data.clear() # Clear cache to get fresh data next time
    except Exception as e:
        st.error(f"บันทึกไม่สำเร็จ: {e}")

# เชื่อมต่อ Database
sh, toast_msg, error_msg, warning_msg = init_connection()

# Display connection status messages
if warning_msg:
    st.warning(warning_msg)
if error_msg:
    st.error(error_msg)
    st.stop() # Stop execution if connection fails
if toast_msg:
    st.toast(toast_msg)


# Load trade history and calculate current holdings
trade_history = load_trade_history(sh)
calculated_qty1, calculated_qty2 = calculate_current_holdings(trade_history)

# ---------------------------------------------------------
# 🎨 SIDEBAR: INPUTS
# ---------------------------------------------------------
with st.sidebar:
    st.title("💼 Trading Inputs")
    st.markdown("---")

    # Form for current portfolio status
    with st.form("portfolio_form"):
        st.subheader("Pair Trading Setup")
        asset1_ticker = st.text_input("Asset 1 Ticker", "GC=F")
        asset2_ticker = st.text_input("Asset 2 Ticker", "SI=F")
        spread_formula = st.text_area("Spread Formula", "(asset2 * 100) - asset1")
        st.caption("Use 'asset1' and 'asset2' in the formula.")

        st.markdown("---")
        st.subheader("Current Status")
        qty_asset1 = st.number_input(f"{asset1_ticker} Holdings", 0.0, value=float(calculated_qty1), step=0.1, format="%.4f")
        qty_asset2 = st.number_input(f"{asset2_ticker} Holdings", 0.0, value=float(calculated_qty2), step=1.0, format="%.4f")
        cash_dca = st.number_input("New Cash / DCA ($)", 0.0, value=1000.0, step=100.0)

        st.markdown("---")
        st.subheader("Target Strategy")
        target_asset1_pct = st.slider(f"Target {asset1_ticker} (%)", 0, 100, 50)
        port_cap = st.number_input("Port Cap ($)", value=20000.0)

        st.markdown("---")
        st.subheader("Technical Settings")
        rolling_window = st.slider("Rolling Window (Days)", 30, 180, 90)
        z_score_high = st.slider("Z-Score High Threshold", 1.0, 3.0, 2.0, 0.1)
        z_score_low = st.slider("Z-Score Low Threshold", -3.0, -1.0, -2.0, 0.1)

        submitted = st.form_submit_button("🔄 Calculate Action")

    target_asset2_pct = 100 - target_asset1_pct

# ---------------------------------------------------------
# 📊 DASHBOARD LAYOUT
# ---------------------------------------------------------
st.title("📈 Smart Pair Trading Manager")

# Load Data
try:
    df = get_market_data(asset1_ticker, asset2_ticker, spread_formula, days=365, rolling_window=rolling_window)
    latest = df.iloc[-1]
    p_asset1, p_asset2, z_score = latest['asset1'], latest['asset2'], latest['Z_Score']
except Exception as e:
    st.error(f"Error loading market data: {e}")
    st.stop()

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Action", "📜 Trade History Log", "📖 คู่มือการใช้งาน"])

with tab1:
    st.subheader("Current Holdings (from History Log)")
    c1, c2 = st.columns(2)
    c1.metric(f"Calculated {asset1_ticker} Holdings", f"{calculated_qty1:.4f}")
    c2.metric(f"Calculated {asset2_ticker} Holdings", f"{calculated_qty2:.4f}")
    # The info note is removed as holdings are now auto-filled in the sidebar
    st.markdown("---")

    st.subheader("Market Status")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{asset1_ticker} Price", f"${p_asset1:,.2f}")
    col2.metric(f"{asset2_ticker} Price", f"${p_asset2:,.2f}")
    col3.metric("Z-Score", f"{z_score:.2f}")
    
    status_text = "Neutral"
    status_color = "off"
    if z_score > z_score_high: status_text, status_color = f"{asset2_ticker} Expensive", "inverse"
    elif z_score < z_score_low: status_text, status_color = f"{asset2_ticker} Cheap", "normal"
    col4.metric("Market Status", status_text, delta_color=status_color)
    st.caption(f"The Z-score indicates how far the current spread is from its {rolling_window}-day average.")

    # 2. Interactive Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], mode='lines', name='Z-Score', line=dict(color='#3182ce')))
    fig.add_hline(y=z_score_high, line_dash="dash", line_color="red")
    fig.add_hline(y=z_score_low, line_dash="dash", line_color="green")
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), title=f"{rolling_window}-Day Z-Score Trend")
    st.plotly_chart(fig, width='stretch')

    # 3. Calculation & Action
    val_asset1, val_asset2, total_val = calculate_portfolio_values(qty_asset1, qty_asset2, p_asset1, p_asset2, cash_dca)
    tgt_asset1, tgt_asset2 = calculate_target_values(total_val, target_asset1_pct, target_asset2_pct)
    diff_asset1, diff_asset2 = calculate_target_diffs(val_asset1, val_asset2, tgt_asset1, tgt_asset2)

    # Action Logic Override by Z-Score
    advice = get_z_score_advice(z_score, z_score_high, z_score_low, asset1_ticker, asset2_ticker)
    st.info(advice)

    # Action Cards
    c1, c2 = st.columns(2)
    act_asset1_str = generate_action_card(c1, asset1_ticker, diff_asset1, p_asset1)
    act_asset2_str = generate_action_card(c2, asset2_ticker, diff_asset2, p_asset2)

    # ---------------------------------------------------------
    # 📝 RECORDING SECTION (ส่วนบันทึกข้อมูล)
    # ---------------------------------------------------------
    st.markdown("### 💾 Record This Transaction")
    st.caption("เมื่อคุณทำการซื้อขายจริงแล้ว กดปุ่มด้านล่างเพื่อบันทึกประวัติลง Google Sheet")
    
    with st.expander("เปิดฟอร์มบันทึก (Transaction Recorder)", expanded=False):
        with st.form("record_trade"):
            r_date = st.date_input("Date", datetime.now())
            r_type = st.selectbox("Action Type", ["DCA Injection", "Rebalance", "Cash Out"])
            r_asset1 = st.text_input(f"{asset1_ticker} Action", value=act_asset1_str if act_asset1_str else "-")
            r_asset2 = st.text_input(f"{asset2_ticker} Action", value=act_asset2_str if act_asset2_str else "-")
            r_note = st.text_input("Note", "")
            
            save_btn = st.form_submit_button("💾 Save to History Log")
            
            if save_btn and sh:
                save_transaction(sh, r_date, r_type, z_score, r_asset1, r_asset2, r_note)

with tab2:
    st.subheader("📜 Transaction History")
    if sh:
        if not trade_history.empty:
            st.dataframe(trade_history, width='stretch')
        else:
            st.info("ยังไม่มีประวัติการเทรดในหน้า Log")
            
    else:
        st.warning("ไม่ได้เชื่อมต่อกับ Google Sheet")

with tab3:
    st.header("📖 คู่มือการใช้งาน")
    st.markdown("""
    ยินดีต้อนรับสู่ **Smart Pair Trading Manager!**

    แอปพลิเคชันนี้เป็นเครื่องมือช่วยวิเคราะห์และจับจังหวะการซื้อขายสำหรับกลยุทธ์ Pair Trading โดยใช้หลักการทางสถิติของ Z-Score เพื่อช่วยให้คุณตัดสินใจลงทุนได้อย่างเป็นระบบ
    """)

    st.subheader("หลักการทำงานของ Z-Score Pair Trading")
    st.markdown("""
    Pair Trading คือกลยุทธ์การเทรดที่อาศัยความสัมพันธ์ของราคาสินทรัพย์สองตัวที่เคลื่อนไหวในทิศทางเดียวกัน (Cointegration) โดยเราจะทำกำไรจาก "ส่วนต่าง" หรือ "Spread" ของราคาสินทรัพย์คู่นั้นๆ เมื่อมันเบี่ยงเบนออกจากค่าเฉลี่ยปกติ
    
    **Z-Score** คือค่าที่บอกว่า Spread ปัจจุบันอยู่ห่างจากค่าเฉลี่ยของมันเป็นระยะทางเท่าไหร่ (ในหน่วยของส่วนเบี่ยงเบนมาตรฐาน)
    - **Z-Score สูง (เช่น > 2.0):** หมายความว่า Spread กว้างกว่าปกติ สินทรัพย์ตัวที่สอง (Asset 2) อาจมีราคาแพงเกินไปเมื่อเทียบกับสินทรัพย์ตัวแรก (Asset 1) -> **กลยุทธ์คือ ขาย Asset 2 และซื้อ Asset 1**
    - **Z-Score ต่ำ (เช่น < -2.0):** หมายความว่า Spread แคบกว่าปกติ สินทรัพย์ตัวที่สอง (Asset 2) อาจมีราคาถูกเกินไปเมื่อเทียบกับสินทรัพย์ตัวแรก (Asset 1) -> **กลยุทธ์คือ ซื้อ Asset 2 และขาย Asset 1**
    - **Z-Score เข้าใกล้ 0:** หมายความว่า Spread กลับเข้าสู่ภาวะปกติ -> **กลยุทธ์คือ ปิดสถานะเพื่อทำกำไร**
    """)

    st.subheader("ส่วนประกอบหลักและวิธีใช้งาน")

    st.markdown("#### 1. 💼 Trading Inputs (แถบด้านข้าง)")
    st.markdown("""
    นี่คือศูนย์ควบคุมหลักของคุณ ประกอบด้วย 4 ส่วน:

    **A. Pair Trading Setup (ตั้งค่าคู่เทรด)**
    -   `Asset 1 Ticker`: Ticker ของสินทรัพย์ตัวแรก (ตัวหลัก)
    -   `Asset 2 Ticker`: Ticker ของสินทรัพย์ตัวที่สอง (ตัวเทียบ)
    -   `Spread Formula`: สูตรคำนวณ Spread
        -   **ตัวอย่าง:**
            -   **Gold vs Silver:** `(asset2 * 100) - asset1` (ใช้ `asset2` (Silver) คูณ 100 เพื่อปรับสเกลให้ใกล้เคียงกับ `asset1` (Gold))
            -   **Stock Pair (e.g., KO vs PEP):** `asset1 - asset2`
            -   **Ratio (e.g., BTC vs ETH):** `asset1 / asset2`
        -   **คำเตือน:** สูตรนี้ใช้ `eval()` ซึ่งมีความเสี่ยง โปรดใช้สูตรจากแหล่งที่เชื่อถือได้เท่านั้น

    **B. Current Status (สถานะพอร์ตปัจจุบัน)**
    -   `... Holdings`: ปริมาณสินทรัพย์ที่คุณถือครองอยู่ **(คุณต้องกรอกค่านี้เอง)** โดยสามารถดูยอดที่คำนวณจากประวัติได้ในหน้า Dashboard หลัก
    -   `New Cash / DCA ($)`: เงินสดใหม่ที่ต้องการเติมเข้าพอร์ต

    **C. Target Strategy (กลยุทธ์เป้าหมาย)**
    -   `Target ... (%)`: สัดส่วนมูลค่าของ Asset 1 ที่คุณต้องการในพอร์ต

    **D. Technical Settings (ตั้งค่าทางเทคนิค)**
    -   `Rolling Window (Days)`: จำนวนวันที่ใช้คำนวณ Z-Score ยิ่งค่าน้อยยิ่งไวต่อการเปลี่ยนแปลงระยะสั้น
    -   `Z-Score High/Low Threshold`: เกณฑ์สำหรับส่งสัญญาณซื้อ/ขาย
    """)

    st.markdown("#### 2. 📊 Dashboard & Action (แท็บหลัก)")
    st.markdown("""
    **A. Current Holdings (from History Log)**
    -   แสดงยอดคงเหลือของแต่ละสินทรัพย์ที่คำนวณจาก `Trade History Log`
    -   **สำคัญ:** นี่คือข้อมูลสำหรับอ้างอิง คุณต้องนำตัวเลขนี้ไปกรอกในช่อง `Holdings` ที่แถบด้านข้างเพื่อให้แอปคำนวณคำแนะนำได้อย่างถูกต้อง

    **B. Market Status (สถานะตลาด)**
    -   แสดงราคาล่าสุดและค่า Z-Score พร้อมบอกสถานะว่าสินทรัพย์ใดถูก/แพง

    **C. Z-Score Trend Chart (กราฟ Z-Score)**
    -   แสดงการเคลื่อนไหวของ Z-Score พร้อมเส้น Threshold เพื่อให้เห็นภาพว่า Spread กำลังเบี่ยงเบนไปในทิศทางใด

    **D. Investment Advice & Action Cards (คำแนะนำและการ์ดดำเนินการ)**
    -   `Investment Advice`: สรุปกลยุทธ์ตามสถานะ Z-Score ปัจจุบัน
    -   `Action Cards`: คำนวณจำนวนเงินและหน่วยที่ต้องซื้อ/ขายอย่างละเอียดเพื่อให้พอร์ตของคุณกลับสู่สัดส่วนเป้าหมาย

    **E. Record This Transaction (บันทึกธุรกรรม)**
    -   ใช้ส่วนนี้เพื่อบันทึกการซื้อ/ขายของคุณลง Google Sheet ซึ่งจะถูกนำไปใช้คำนวณใน "Current Holdings" ครั้งถัดไป
    """)
    
    st.subheader("การแก้ไขปัญหา (Troubleshooting)")
    st.markdown("""
    -   **ยอด Holdings ที่คำนวณเป็น 0 ทั้งๆ ที่มีประวัติ:**
        1.  ไปที่แท็บ `Trade History Log`
        2.  เปิดส่วน `Show Raw History Data (for Debugging)`
        3.  **ตรวจสอบคอลัมน์:** ตรวจสอบว่าชื่อคอลัมน์ใน Google Sheet ของคุณมี `asset1_action` และ `asset2_action` (หรือ `Gold Action` และ `Silver Action` สำหรับข้อมูลเก่า)
        4.  **ตรวจสอบรูปแบบข้อมูล:** ข้อมูลในคอลัมน์ action ต้องอยู่ในรูปแบบ `BUY:1.23` หรือ `SELL 4.56` (คั่นด้วย `:` หรือ ` `) และตามด้วยตัวเลขที่ถูกต้อง
    """)