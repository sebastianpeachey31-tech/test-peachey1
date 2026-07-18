"""
Excel 导出模块
"""
import os
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def export_to_excel(records, filepath=None):
    """
    将记录导出为 Excel 文件（包含支出和收入）。
    """
    if not HAS_OPENPYXL:
        raise ImportError("请先安装 openpyxl：pip install openpyxl")

    wb = Workbook()
    ws = wb.active
    ws.title = "账单明细"

    # ---- 样式 ----
    header_font = Font(name='Microsoft YaHei', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )
    green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
    red_font = Font(name='Microsoft YaHei', size=10, color='C00000')

    # ---- 表头 ----
    headers = ['日期', '类型', '一级分类', '二级分类', '金额（元）', '备注']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # ---- 数据行 ----
    total_expense = 0
    total_income = 0

    for row, rec in enumerate(records, 2):
        type_text = "收入" if rec.get('type') == 'income' else "支出"
        amount = rec['amount']

        ws.cell(row=row, column=1, value=rec['date']).border = thin_border
        ws.cell(row=row, column=2, value=type_text).border = thin_border
        ws.cell(row=row, column=3, value=rec['category_l1']).border = thin_border
        ws.cell(row=row, column=4, value=rec['category_l2']).border = thin_border
        ws.cell(row=row, column=5, value=amount).border = thin_border
        ws.cell(row=row, column=6, value=rec['note'] or '').border = thin_border

        for col in range(1, 7):
            ws.cell(row=row, column=col).alignment = Alignment(horizontal='center', vertical='center')

        # 收入行绿色背景
        if rec.get('type') == 'income':
            for col in range(1, 7):
                ws.cell(row=row, column=col).fill = green_fill
            total_income += amount
        else:
            total_expense += amount

    # ---- 列宽 ----
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 8
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 30

    # ---- 合计行 ----
    total_row = len(records) + 2

    # 支出合计
    ws.cell(row=total_row, column=3, value='支出合计').font = Font(bold=True, name='Microsoft YaHei')
    ws.cell(row=total_row, column=3).alignment = Alignment(horizontal='center')
    ws.cell(row=total_row, column=3).border = thin_border
    cell_e = ws.cell(row=total_row, column=5, value=round(total_expense, 2))
    cell_e.font = Font(bold=True, name='Microsoft YaHei', color='C00000')
    cell_e.alignment = Alignment(horizontal='center')
    cell_e.border = thin_border

    # 收入合计
    total_row2 = total_row + 1
    ws.cell(row=total_row2, column=3, value='收入合计').font = Font(bold=True, name='Microsoft YaHei')
    ws.cell(row=total_row2, column=3).alignment = Alignment(horizontal='center')
    ws.cell(row=total_row2, column=3).border = thin_border
    cell_i = ws.cell(row=total_row2, column=5, value=round(total_income, 2))
    cell_i.font = Font(bold=True, name='Microsoft YaHei', color='006100')
    cell_i.alignment = Alignment(horizontal='center')
    cell_i.border = thin_border

    # 结余
    total_row3 = total_row2 + 1
    balance = total_income - total_expense
    ws.cell(row=total_row3, column=3, value='结余').font = Font(bold=True, name='Microsoft YaHei')
    ws.cell(row=total_row3, column=3).alignment = Alignment(horizontal='center')
    ws.cell(row=total_row3, column=3).border = thin_border
    cell_b = ws.cell(row=total_row3, column=5, value=round(balance, 2))
    cell_b.font = Font(bold=True, name='Microsoft YaHei', color='0070C0')
    cell_b.alignment = Alignment(horizontal='center')
    cell_b.border = thin_border

    # ---- 保存 ----
    if filepath is None:
        # 默认导出到项目根目录（test peachey1）
        qiangge_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.dirname(qiangge_dir)  # 项目根目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(save_dir, f"强哥帮你记_账单_{timestamp}.xlsx")

    wb.save(filepath)
    return filepath
