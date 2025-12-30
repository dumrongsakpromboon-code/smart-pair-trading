import pandas as pd
import xlsxwriter

# ชื่อไฟล์ผลลัพธ์
output_file = 'Bakery_System_Corrected.xlsx'

# สร้าง Excel Writer
workbook = xlsxwriter.Workbook(output_file)

# --- Formats (กำหนดรูปแบบ) ---
fmt_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D9EAD3', 'border': 1, 'valign': 'vcenter'})
fmt_currency = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
fmt_pct = workbook.add_format({'num_format': '0%', 'align': 'center', 'border': 1})
fmt_center = workbook.add_format({'align': 'center', 'border': 1})
fmt_text = workbook.add_format({'border': 1})
fmt_bold_curr = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'align': 'right', 'border': 1, 'bg_color': '#FFF2CC'})
fmt_title = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#274E13'})
fmt_card_head = workbook.add_format({'bold': True, 'bg_color': '#CFE2F3', 'border': 1})

# ==========================================
# Sheet 1: Inventory (สต็อกวัตถุดิบ)
# ==========================================
ws_inv = workbook.add_worksheet('1_Inventory')
ws_inv.set_column('B:B', 30)
ws_inv.set_column('C:G', 15)

# Headers
headers_inv = ['ID', 'Material Name', 'Purchase Price', 'Qty', 'Unit', 'Grams per Unit', 'Cost/Gram']
ws_inv.write_row(1, 0, headers_inv, fmt_header)
ws_inv.write(0, 0, 'INVENTORY MASTER', fmt_title)

# Mock Data
materials = [
    ['M001', 'แป้งเค้ก (Cake Flour)', 45, 1, 'kg', 1000],
    ['M002', 'น้ำตาลทราย (Sugar)', 24, 1, 'kg', 1000],
    ['M003', 'เนยสด (Butter)', 180, 1, 'kg', 1000],
    ['M004', 'ไข่ไก่ (Eggs)', 120, 30, 'pcs', 55],  # เฉลี่ย 55g ต่อฟอง
    ['M005', 'นมสด (Milk)', 95, 2, 'L', 1000],
    ['M006', 'ผงโกโก้ (Cocoa)', 350, 1, 'kg', 1000],
    ['M007', 'สตรอว์เบอร์รี (Strawberry)', 250, 1, 'kg', 1000],
    ['M008', 'วิปครีม (Whipping Cream)', 160, 1, 'L', 1000]
]

for i, mat in enumerate(materials):
    row = i + 2
    ws_inv.write(row, 0, mat[0], fmt_center)
    ws_inv.write(row, 1, mat[1], fmt_text)
    ws_inv.write(row, 2, mat[2], fmt_currency)
    ws_inv.write(row, 3, mat[3], fmt_center)
    ws_inv.write(row, 4, mat[4], fmt_center)
    ws_inv.write(row, 5, mat[5], fmt_center)
    # Formula Cost/Gram: Price / (Qty * Grams)
    # Excel Row = row+1
    ws_inv.write_formula(row, 6, f'=C{row+1}/(D{row+1}*F{row+1})', fmt_currency)

# ==========================================
# Sheet 2: Recipe_Master (สูตรและต้นทุน)
# ==========================================
ws_recipe = workbook.add_worksheet('2_Recipe_Master')
ws_recipe.set_column('B:B', 30)
ws_recipe.set_column('C:F', 18)

ws_recipe.write(0, 0, 'MENU PRICING SUMMARY', fmt_title)
headers_summary = ['ID', 'Menu Name', 'Total Cost', 'Target Margin %', 'Rec. Price', 'Final Price']
ws_recipe.write_row(1, 0, headers_summary, fmt_header)

menus = [
    ('MN01', 'Strawberry Shortcake', 0.60),
    ('MN02', 'Double Choc Brownie', 0.55),
    ('MN03', 'Oatmeal Cookie', 0.50),
    ('MN04', 'Butter Croissant', 0.50),
    ('MN05', 'Coconut Pie', 0.60)
]

# กำหนดตำแหน่งเริ่มต้นของการ์ดสูตรด้านล่าง (เริ่มที่บรรทัด 12)
card_start_row = 12 
card_gap = 14 # ระยะห่างระหว่างการ์ด

for i, (mid, name, margin) in enumerate(menus):
    # --- 1. เขียนตารางสรุปด้านบน (Summary Table) ---
    sum_row = i + 2
    ws_recipe.write(sum_row, 0, mid, fmt_center)
    ws_recipe.write(sum_row, 1, name, fmt_text)
    
    # คำนวณตำแหน่งที่ Total Cost ของการ์ดนี้จะอยู่
    # Logic: Card Start + (i * gap) + บรรทัดที่เป็น Total Cost (ประมาณบรรทัดที่ 9 ของการ์ด)
    current_card_top = card_start_row + (i * card_gap)
    total_cost_cell_ref = f'E{current_card_top + 10}' # +10 คือตำแหน่งบรรทัด Total Cost ในการ์ด
    
    # Link Cost ขึ้นมา
    ws_recipe.write_formula(sum_row, 2, f'={total_cost_cell_ref}', fmt_currency)
    
    # Margin
    ws_recipe.write(sum_row, 3, margin, fmt_pct)
    
    # Formula Pricing (Corrected): Cost / (1 - Margin)
    ws_recipe.write_formula(sum_row, 4, f'=C{sum_row+1}/(1-D{sum_row+1})', fmt_currency)
    
    # Final Price (Manual) - Default ให้เท่ากับแนะนำ
    ws_recipe.write_formula(sum_row, 5, f'=E{sum_row+1}', fmt_bold_curr)

    # --- 2. เขียนการ์ดสูตรด้านล่าง (Recipe Cards) ---
    c_row = current_card_top
    ws_recipe.write(c_row, 0, f'RECIPE: {name} ({mid})', fmt_card_head)
    
    # Card Headers
    card_headers = ['Ingredient', 'Qty (g)', 'Cost/g (Link)', 'Line Cost', 'Notes']
    ws_recipe.write_row(c_row+1, 0, card_headers, fmt_header)
    
    # Ingredients Rows (5 rows placeholder)
    for r in range(5):
        ing_row = c_row + 2 + r
        # ใส่ VLOOKUP Dummy หรือเว้นว่างให้กรอก
        # สมมติให้ Link ไป Inventory แบบง่ายๆ หรือใส่ 0 ไว้ก่อน
        ws_recipe.write(ing_row, 0, '', fmt_text) # ชื่อวัตถุดิบ
        ws_recipe.write(ing_row, 1, 0, fmt_center) # ปริมาณ
        # Cost/g: ลองใส่สูตร VLOOKUP ไว้ (แต่ถ้าว่างจะเป็น 0)
        # =IFERROR(VLOOKUP(A_Row, Inventory, 7, FALSE), 0)
        ws_recipe.write_formula(ing_row, 2, f'=IFERROR(VLOOKUP(A{ing_row+1},\'1_Inventory\'!$B$3:$G$20,6,FALSE),0)', fmt_currency)
        # Line Cost
        ws_recipe.write_formula(ing_row, 3, f'=B{ing_row+1}*C{ing_row+1}', fmt_currency)

    # Summary Section of Card
    sub_total_row = c_row + 7
    ws_recipe.write(sub_total_row, 2, 'Raw Material Cost', fmt_header)
    ws_recipe.write_formula(sub_total_row, 3, f'=SUM(D{c_row+3}:D{c_row+7})', fmt_currency)
    
    loss_row = c_row + 8
    ws_recipe.write(loss_row, 2, 'Loss % (Yield)', fmt_header)
    ws_recipe.write(loss_row, 3, 0.10, fmt_pct) # Default Loss 10%
    
    total_row = c_row + 9
    ws_recipe.write(total_row, 2, 'TOTAL COST / PCS', fmt_bold_curr)
    # Formula Loss (Corrected): Raw Cost / (1 - Loss)
    ws_recipe.write_formula(total_row, 3, f'=D{sub_total_row+1}/(1-D{loss_row+1})', fmt_bold_curr)

# ==========================================
# Sheet 3: Daily Sales (บันทึกยอดขาย)
# ==========================================
ws_sales = workbook.add_worksheet('3_Daily_Sales')
ws_sales.set_column('B:B', 25)
ws_sales.set_column('C:H', 15)

ws_sales.write(0, 0, 'DAILY SALES LOG', fmt_title)
sales_headers = ['Date', 'Menu Item', 'Qty Sold', 'Selling Price', 'Cost per Unit', 'Total Sales', 'Total Cost', 'Gross Profit']
ws_sales.write_row(1, 0, sales_headers, fmt_header)

# Data Validation
ws_sales.data_validation('B3:B100', {'validate': 'list', 'source': '=\'2_Recipe_Master\'!$B$3:$B$7'})

# Formulas for 20 rows
for r in range(2, 22):
    row_idx = r + 1
    # VLOOKUP Price (Col F in Recipe Master, Index 6)
    ws_sales.write_formula(r, 3, f'=IFERROR(VLOOKUP(B{row_idx},\'2_Recipe_Master\'!$B$3:$F$7,5,FALSE),0)', fmt_currency)
    # VLOOKUP Cost (Col C in Recipe Master, Index 3)
    ws_sales.write_formula(r, 4, f'=IFERROR(VLOOKUP(B{row_idx},\'2_Recipe_Master\'!$B$3:$F$7,2,FALSE),0)', fmt_currency)
    
    # Total Sales
    ws_sales.write_formula(r, 5, f'=C{row_idx}*D{row_idx}', fmt_currency)
    # Total Cost
    ws_sales.write_formula(r, 6, f'=C{row_idx}*E{row_idx}', fmt_currency)
    # Gross Profit
    ws_sales.write_formula(r, 7, f'=F{row_idx}-G{row_idx}', fmt_currency)

# ==========================================
# Sheet 4: Dashboard
# ==========================================
ws_dash = workbook.add_worksheet('4_Dashboard')
ws_dash.write(0, 0, 'BUSINESS SNAPSHOT', fmt_title)

ws_dash.write(2, 0, 'Total Revenue', fmt_header)
ws_dash.write_formula(2, 1, '=SUM(\'3_Daily_Sales\'!F:F)', fmt_currency)

ws_dash.write(3, 0, 'Total Cost', fmt_header)
ws_dash.write_formula(3, 1, '=SUM(\'3_Daily_Sales\'!G:G)', fmt_currency)

ws_dash.write(4, 0, 'Net Profit', fmt_header)
ws_dash.write_formula(4, 1, '=SUM(\'3_Daily_Sales\'!H:H)', fmt_bold_curr)

workbook.close()
print(f"File '{output_file}' generated successfully with corrected formulas.")