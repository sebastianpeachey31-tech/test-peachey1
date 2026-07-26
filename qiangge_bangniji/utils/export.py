"""
Excel 导出模块 — 把记账记录导出为 .xlsx 文件。
依赖 openpyxl 库（pip install openpyxl）。
"""
import os
from datetime import datetime

# 尝试导入 openpyxl 库，如果没安装就记个标记，调用时再报错
try:
    from openpyxl import Workbook          # Workbook = 一个 Excel 文件
    from openpyxl.styles import (
        Font, PatternFill, Alignment,     # Font=字体样式, PatternFill=单元格底色, Alignment=对齐方式
        Border, Side                       # Border=单元格边框, Side=边框线条样式
    )
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def export_to_excel(records, filepath=None):
    """将账单记录导出为 Excel 文件（.xlsx 格式）。

    导出的表格包含：日期、类型（支出/收入）、一级分类、二级分类、
    金额、备注，末尾有支出合计、收入合计、结余三行。收入行用绿色
    背景标记，支出合计用红色字体。

    参数：
        records: 记录列表，每条是一个字典（从数据库查出来的）
        filepath: 保存路径（可选），不填则自动生成到桌面

    返回：
        实际保存的文件路径
    """
    if not HAS_OPENPYXL:
        raise ImportError("请先安装 openpyxl：pip install openpyxl")

    wb = Workbook()       # 创建一个空白的 Excel 文件
    ws = wb.active         # 获取默认的工作表（Sheet）
    ws.title = "账单明细"  # 给工作表起个名字

    # ---- 样式定义（用 openpyxl 的样式对象美化表格）----
    # 表头样式：微软雅黑、11号、加粗、白色字、蓝色底
    header_font = Font(name='Microsoft YaHei', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center')
    # 细线边框，给每个单元格画"田"字格
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )
    # 收入行用浅绿色背景，一眼就能区分支出（白底）和收入（绿底）
    green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
    # 支出金额用深红色字体
    red_font = Font(name='Microsoft YaHei', size=10, color='C00000')

    # ---- 表头 ----
    headers = ['日期', '类型', '一级分类', '二级分类', '金额（元）', '备注']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # ---- 数据行：逐条写入记录 ----
    total_expense = 0   # 累计支出金额
    total_income = 0     # 累计收入金额

    for row, rec in enumerate(records, 2):  # 从第 2 行开始写（第 1 行是表头）
        type_text = "收入" if rec.get('type') == 'income' else "支出"
        amount = rec['amount']

        # 依次写入：日期、类型、一级分类、二级分类、金额、备注
        ws.cell(row=row, column=1, value=rec['date']).border = thin_border
        ws.cell(row=row, column=2, value=type_text).border = thin_border
        ws.cell(row=row, column=3, value=rec['category_l1']).border = thin_border
        ws.cell(row=row, column=4, value=rec['category_l2']).border = thin_border
        ws.cell(row=row, column=5, value=amount).border = thin_border
        ws.cell(row=row, column=6, value=rec['note'] or '').border = thin_border

        # 所有列居中对齐
        for col in range(1, 7):
            ws.cell(row=row, column=col).alignment = Alignment(horizontal='center', vertical='center')

        # 收入行加绿色背景，方便和支出行区分
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

    # ---- 保存文件 ----
    if filepath is None:
        # 没指定路径时，自动导出到程序所在目录
        qiangge_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.dirname(qiangge_dir)  # 项目根目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(save_dir, f"强哥帮你记_账单_{timestamp}.xlsx")

    wb.save(filepath)
    return filepath
