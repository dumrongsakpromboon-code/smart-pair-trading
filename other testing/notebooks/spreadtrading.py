
import gspread
import time

# --- CONFIGURATION ---
SPREADSHEET_NAME = "Smart_Portfolio_ZScore_Edition"
CREDENTIALS_FILE = 'client_secret.json' # ต้องวางไฟล์นี้คู่กับ script

def create_zscore_sheet_oauth():
    print("🔐 กำลังเชื่อมต่อ Google ผ่าน OAuth 2.0...")
    print("👉 (หากมีหน้าต่างเด้งขึ้นมา ให้กดเลือกบัญชี Google และกด Allow)")
    
    try:
        # ระบบจะสร้าง token.json อัตโนมัติหลัง login ครั้งแรก
        client = gspread.oauth(
            credentials_filename=CREDENTIALS_FILE,
            authorized_user_filename='token.json'
        )
    except Exception as e:
        print(f"❌ Error Login: {e}")
        print("ตรวจสอบว่ามีไฟล์ client_secret.json หรือยัง")
        return

    print(f"🚀 กำลังสร้างไฟล์: {SPREADSHEET_NAME} ...")
    sh = client.create(SPREADSHEET_NAME)
    
    # ---------------------------------------------------------
    # TAB 1: CALC ENGINE (ระบบคำนวณสถิติหลังบ้าน)
    # ---------------------------------------------------------
    ws_calc = sh.sheet1
    ws_calc.update_title("Calc_Engine")
    ws_calc.update('A1:F1', [["Date", "Gold History", "Silver History", "Spread", "Mean (90d)", "SD (90d)"]])
    
    # สูตรดึงข้อมูลย้อนหลัง 150 วัน และคำนวณค่าทางสถิติ (Mean, SD)
    ws_calc.update_acell('A2', '=QUERY(GOOGLEFINANCE("CURRENCY:XAUUSD", "price", TODAY()-150, TODAY()), "SELECT Col1, Col2 LABEL Col1 \'\', Col2 \'\'")')
    ws_calc.update_acell('C2', '=INDEX(GOOGLEFINANCE("CURRENCY:XAGUSD", "price", TODAY()-150, TODAY()), 0, 2)')
    ws_calc.update_acell('D2', '=ARRAYFORMULA(IF(ISNUMBER(B2:B), (C2:C*100)-B2:B, ""))')
    ws_calc.update_acell('E2', '=AVERAGE(QUERY(D2:D, "SELECT D WHERE D IS NOT NULL ORDER BY D DESC LIMIT 90"))')
    ws_calc.update_acell('F2', '=STDEV(QUERY(D2:D, "SELECT D WHERE D IS NOT NULL ORDER BY D DESC LIMIT 90"))')

    # ---------------------------------------------------------
    # TAB 2: DASHBOARD (หน้าจอหลัก)
    # ---------------------------------------------------------
    ws_dash = sh.add_worksheet(title="Dashboard", rows=50, cols=10)
    
    data = [
        ["1. Market Statistics (Z-Score)", "Value"],
        ["Gold Price", '=GOOGLEFINANCE("CURRENCY:XAUUSD")'],
        ["Silver Price", '=GOOGLEFINANCE("CURRENCY:XAGUSD")'],
        ["Spread Raw", '=(B3*100)-B2'],
        ["Z-Score Status", '=(B4 - Calc_Engine!E2) / Calc_Engine!F2'], # สูตร Z-Score หัวใจสำคัญ
        ["", ""],
        ["2. My Portfolio", "Units / USD"],
        ["Gold Holdings (oz)", 0],
        ["Silver Holdings (oz)", 0],
        ["Cash / DCA Amount ($)", 1000],
        ["", ""],
        ["3. Strategy Target", "Plan"],
        ["Target Gold (%)", 50],
        ["Target Silver (%)", '=100-B13'],
        ["", ""],
        ["4. AI Recommendation", "Action"],
        ["GOLD ACTION", ""],
        ["SILVER ACTION", ""],
        ["", ""],
        ["5. Limits", "USD"],
        ["Portfolio Cap (Cash Out)", 20000]
    ]
    ws_dash.update('A1:B21', data)

    # สูตร AI ตัดสินใจ (Logic: ซื้อ/ขาย เมื่อ Z-Score ทะลุ +- 2.0)
    f_gold = '=LET(z, B5, total, (B8*B2)+(B9*B3)+B10, tgt, total*(B13/100), cur, B8*B2, diff, tgt-cur, IF(z > 2, "BUY (Silver Expensive)", IF(z < -2, "SELL (Silver Cheap)", IF(diff>0, "DCA Buy", "Wait/Sell"))))'
    f_silver = '=LET(z, B5, total, (B8*B2)+(B9*B3)+B10, tgt, total*(B14/100), cur, B9*B3, diff, tgt-cur, IF(z > 2, "SELL (Silver Expensive)", IF(z < -2, "BUY (Silver Cheap)", IF(diff>0, "DCA Buy", "Wait/Sell"))))'

    ws_dash.update_acell('B17', f_gold)
    ws_dash.update_acell('B18', f_silver)
    
    # Formatting พื้นฐาน
    ws_dash.format('B5', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 1}})

    # ---------------------------------------------------------
    # TAB 3: LOG (บันทึกประวัติ)
    # ---------------------------------------------------------
    ws_log = sh.add_worksheet(title="History_Log", rows=1000, cols=6)
    ws_log.append_row(["Date", "Action Type", "Z-Score", "Gold Action", "Silver Action", "Note"])

    print(f"\n✅ สร้างไฟล์สำเร็จ! ชื่อ: '{SPREADSHEET_NAME}'")
    print(f"🔗 ลิงก์: https://docs.google.com/spreadsheets/d/{sh.id}")

if __name__ == "__main__":
    create_zscore_sheet_oauth()