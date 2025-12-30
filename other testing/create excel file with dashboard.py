import xlsxwriter
import datetime

# ชื่อไฟล์ผลลัพธ์
output_file = 'Bakery_Pro_Dashboard.xlsx'

# สร้าง Excel Writer
workbook = xlsxwriter.Workbook(output_file)

# --- Formats (Styles) ---
# Main Headers
fmt_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D9EAD3', 'border': 1, 'valign': 'vcenter'})
fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#274E13'})
fmt_subtitle = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#555555', 'underline': True})

# Data Formats
fmt_currency = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
fmt_pct = workbook.add_format({'num_format': '0%', 'align': 'center', 'border': 1})
fmt_center = workbook.add_format({'align': 'center', 'border': 1})
fmt_text = workbook.add_format({'border': 1})

# Dashboard Specific Formats
fmt_card_label = workbook.add_format({'align': 'left', 'font_size': 10, 'font_color': '#666666', 'bg_color': '#FFFFFF', 'top': 1, 'left': 1, 'right': 1})
fmt_card_value = workbook.add_format({'bold': True, 'align': 'left', 'font_size': 14, 'num_format': '#,##0.00', 'bg_color': '#FFFFFF', 'bottom': 1, 'left': 1, 'right': 1})
fmt_card_value_pct = workbook.add_format({'bold': True, 'align': 'left', 'font_size': 14, 'num_format': '0.00%', 'bg_color': '#FFFFFF', 'bottom': 1, 'left': 1, 'right': 1})

# ==========================================
# Sheet 1: Inventory (เหมือนเดิม)
# ==========================================
ws_inv = workbook.add_worksheet('1_Inventory')
ws_inv.set_column('B:B', 25)
ws_inv.set_column('C:G', 12)
ws_inv.write(0, 0, 'INVENTORY MASTER', fmt_title)
headers_inv = ['ID', 'Material Name', 'Purchase Price', 'Qty', 'Unit', 'G/Unit', 'Cost/Gram']
ws_inv.write_row(1, 0, headers_inv, fmt_header)
materials = [
    ['M001', 'แป้งเค้ก', 45, 1, 'kg', 1000], ['M002', 'น้ำตาลทราย', 24, 1, 'kg', 1000],
    ['M003', 'เนยสด', 180, 1, 'kg', 1000], ['M004', 'ไข่ไก่', 120, 30, 'pcs', 55],
    ['M005', 'นมสด', 95, 2, 'L', 1000], ['M006', 'สตรอว์เบอร์รี', 250, 1, 'kg', 1000]
]
for i, mat in enumerate(materials):
    r = i + 2
    ws_inv.write_row(r, 0, mat[:6], fmt_center)
    ws_inv.write_formula(r, 6, f'=C{r+1}/(D{r+1}*F{r+1})', fmt_currency)

# ==========================================
# Sheet 2: Recipe_Master (เหมือนเดิม + แก้สูตร)
# ==========================================
ws_recipe = workbook.add_worksheet('2_Recipe_Master')
ws_recipe.set_column('B:B', 30)
ws_recipe.set_column('C:F', 15)
ws_recipe.write(0, 0, 'MENU PRICING', fmt_title)
headers_sum = ['ID', 'Menu Name', 'Total Cost', 'Target Margin', 'Rec. Price', 'Final Price']
ws_recipe.write_row(1, 0, headers_sum, fmt_header)
menus = [
    ('MN01', 'Strawberry Shortcake', 0.60), ('MN02', 'Double Choc Brownie', 0.55),
    ('MN03', 'Oatmeal Cookie', 0.50), ('MN04', 'Butter Croissant', 0.50), ('MN05', 'Coconut Pie', 0.60)
]
card_start = 10
for i, (mid, name, margin) in enumerate(menus):
    # Summary Table
    r = i + 2
    top_card = card_start + (i*12)
    total_cost_ref = f'E{top_card+9}' # Link to card total
    ws_recipe.write(r, 0, mid, fmt_center)
    ws_recipe.write(r, 1, name, fmt_text)
    ws_recipe.write_formula(r, 2, f'={total_cost_ref}', fmt_currency)
    ws_recipe.write(r, 3, margin, fmt_pct)
    ws_recipe.write_formula(r, 4, f'=C{r+1}/(1-D{r+1})', fmt_currency) # Formula: Cost/(1-Margin)
    ws_recipe.write_formula(r, 5, f'=E{r+1}', workbook.add_format({'num_format':'#,##0.00','bg_color':'#FFF2CC','border':1}))
    
    # Recipe Card
    ws_recipe.write(top_card, 0, f'RECIPE: {name}', workbook.add_format({'bold':True,'bg_color':'#CFE2F3'}))
    ws_recipe.write_row(top_card+1, 0, ['Ing', 'Qty(g)', 'Cost/g', 'Line Cost'], fmt_header)
    for row_ing in range(5):
        curr = top_card + 2 + row_ing
        ws_recipe.write_formula(curr, 2, f'=IFERROR(VLOOKUP(A{curr+1},\'1_Inventory\'!$B$3:$G$20,6,FALSE),0)', fmt_currency)
        ws_recipe.write_formula(curr, 3, f'=B{curr+1}*C{curr+1}', fmt_currency)
    
    ws_recipe.write(top_card+7, 2, 'Raw Cost', fmt_header)
    ws_recipe.write_formula(top_card+7, 3, f'=SUM(D{top_card+3}:D{top_card+7})', fmt_currency)
    ws_recipe.write(top_card+8, 2, 'Total (Loss 10%)', fmt_header)
    ws_recipe.write_formula(top_card+8, 3, f'=D{top_card+8}/0.9', fmt_currency) # Loss Formula

# ==========================================
# Sheet 3: Daily_Sales (เหมือนเดิม)
# ==========================================
ws_sales = workbook.add_worksheet('3_Daily_Sales')
ws_sales.set_column('B:B', 25)
ws_sales.set_column('F:H', 12)
ws_sales.write(0, 0, 'DAILY SALES LOG', fmt_title)
ws_sales.write_row(1, 0, ['Date', 'Item', 'Qty', 'Price', 'Cost', 'Total Sales', 'Total Cost', 'Profit'], fmt_header)
ws_sales.data_validation('B3:B100', {'validate':'list', 'source':'=\'2_Recipe_Master\'!$B$3:$B$7'})
for r in range(2, 52): # 50 rows
    idx = r+1
    ws_sales.write_formula(r, 3, f'=IFERROR(VLOOKUP(B{idx},\'2_Recipe_Master\'!$B$3:$F$7,5,FALSE),0)', fmt_currency)
    ws_sales.write_formula(r, 4, f'=IFERROR(VLOOKUP(B{idx},\'2_Recipe_Master\'!$B$3:$F$7,2,FALSE),0)', fmt_currency)
    ws_sales.write_formula(r, 5, f'=C{idx}*D{idx}', fmt_currency)
    ws_sales.write_formula(r, 6, f'=C{idx}*E{idx}', fmt_currency)
    ws_sales.write_formula(r, 7, f'=F{idx}-G{idx}', fmt_currency)

# ==========================================
# Sheet 4: DASHBOARD (ส่วนที่เพิ่มใหม่)
# ==========================================
ws_dash = workbook.add_worksheet('4_Dashboard')
ws_dash.hide_gridlines(2) # ซ่อนเส้นตารางให้ดูสะอาดตา
ws_dash.set_column('A:A', 2) # Margin Left
ws_dash.set_column('B:I', 14) # Card Widths

ws_dash.write(0, 1, 'OWNER DASHBOARD', fmt_title)
ws_dash.write(0, 7, 'Last Update: Live', workbook.add_format({'align':'right', 'italic':True}))

# --- 1. KPI Cards Section ---
cards = [
    ('Total Revenue', '=SUM(\'3_Daily_Sales\'!F:F)', fmt_card_value),
    ('Total Cost', '=SUM(\'3_Daily_Sales\'!G:G)', fmt_card_value),
    ('Net Profit', '=SUM(\'3_Daily_Sales\'!H:H)', fmt_card_value),
    ('Avg Margin %', '=IF(B4=0,0,F4/B4)', fmt_card_value_pct)
]

# วาง Card ที่บรรทัด 3 (Row index 2, 3)
for i, (label, formula, fmt) in enumerate(cards):
    col = 1 + (i * 2) # เว้นระยะทีละ 2 คอลัมน์ (B, D, F, H)
    ws_dash.merge_range(2, col, 2, col+1, label, fmt_card_label) # Label Row
    ws_dash.merge_range(3, col, 3, col+1, formula, fmt) # Value Row

# --- 2. Data Calculation Area (Hidden or Side Table) ---
# เราต้องสร้างตารางสรุปยอดขายรายเมนูเพื่อนำไปทำกราฟ (วางไว้ด้านขวาของ Dashboard)
table_start_col = 10 # Column K
ws_dash.write(2, table_start_col, 'Menu Analysis', fmt_subtitle)
ws_dash.write_row(3, table_start_col, ['Menu Name', 'Total Qty', 'Total Sales'], fmt_header)

# ดึงชื่อเมนูมาจาก Sheet Recipe และใช้ SUMIF คำนวณยอดขาย
for i in range(5):
    r = 4 + i
    # Link ชื่อเมนูจาก Recipe Master
    ws_dash.write_formula(r, table_start_col, f'=\'2_Recipe_Master\'!B{i+3}', fmt_text)
    # SUMIF Quantity
    ws_dash.write_formula(r, table_start_col+1, f'=SUMIF(\'3_Daily_Sales\'!B:B, K{r+1}, \'3_Daily_Sales\'!C:C)', fmt_center)
    # SUMIF Sales Amount
    ws_dash.write_formula(r, table_start_col+2, f'=SUMIF(\'3_Daily_Sales\'!B:B, K{r+1}, \'3_Daily_Sales\'!F:F)', fmt_currency)

# --- 3. Charts Section ---

# Chart 1: Top Selling Menu (Bar Chart)
chart1 = workbook.add_chart({'type': 'column'})
chart1.add_series({
    'name':       'Sales Amount',
    'categories': ['4_Dashboard', 4, table_start_col, 8, table_start_col],   # ชื่อเมนู
    'values':     ['4_Dashboard', 4, table_start_col+2, 8, table_start_col+2], # ยอดขายรวม
    'fill':       {'color': '#6D9EEB'}
})
chart1.set_title({'name': 'Best Selling Menus (ยอดขายตามเมนู)'})
chart1.set_legend({'none': True})
ws_dash.insert_chart('B6', chart1, {'x_scale': 1.8, 'y_scale': 1.2})

# Chart 2: Daily Profit Trend (Line Chart)
# ดึงข้อมูล 20 วันแรกจาก Daily Sales มาพลอตกราฟ
chart2 = workbook.add_chart({'type': 'line'})
chart2.add_series({
    'name':   'Daily Profit',
    'categories': ['3_Daily_Sales', 2, 0, 21, 0], # วันที่ (Col A)
    'values':     ['3_Daily_Sales', 2, 7, 21, 7], # กำไรสุทธิ (Col H)
    'line':       {'color': '#4CAF50', 'width': 2.25},
    'marker':     {'type': 'circle', 'size': 5}
})
chart2.set_title({'name': 'Profit Trend (แนวโน้มกำไร 20 รายการล่าสุด)'})
chart2.set_x_axis({'name': 'Date'})
chart2.set_y_axis({'name': 'Profit (THB)', 'major_gridlines': {'visible': True}})
ws_dash.insert_chart('B25', chart2, {'x_scale': 1.8, 'y_scale': 1.2})

workbook.close()
print(f"File '{output_file}' generated successfully with Dashboard.")