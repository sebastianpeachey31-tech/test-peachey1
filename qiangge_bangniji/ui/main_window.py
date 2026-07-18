"""
主窗口界面 - "强哥帮你记"的核心界面。
左边是记账表单，右边是统计和账单列表。
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
import os
import sys

# matplotlib 用于饼图
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import (
    init_db, EXPENSE_CATEGORIES, INCOME_CATEGORIES,
    add_record, get_all_records, update_record, delete_record,
    get_records_by_date_range, get_records_by_category, get_monthly_stats
)

# 颜色常量
COLOR_EXPENSE = '#E74C3C'   # 支出红
COLOR_INCOME = '#27AE60'    # 收入绿


class MainWindow:
    """主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title("强哥帮你记")
        self.root.geometry("1200x750")
        self.root.minsize(950, 550)

        # 当前收支类型
        self.record_type = "expense"
        # 当前编辑中的记录ID
        self.editing_id = None

        # 初始化数据库
        init_db()

        # 构建界面
        self._build_ui()

        # 加载数据
        self._load_records()
        self._update_stats()

    # ================================================================
    # 界面构建
    # ================================================================

    def _build_ui(self):
        """构建完整界面布局"""

        # ---- 顶部标题栏 ----
        title_bar = ttk.Frame(self.root)
        title_bar.pack(fill=tk.X, padx=20, pady=(15, 5))

        ttk.Label(
            title_bar, text="💰 强哥帮你记",
            font=('Microsoft YaHei', 18, 'bold'),
            bootstyle="primary"
        ).pack(side=tk.LEFT)

        ttk.Label(
            title_bar, text="每一笔，强哥都帮你记着",
            font=('Microsoft YaHei', 9), bootstyle="secondary"
        ).pack(side=tk.LEFT, padx=(15, 0))

        # ---- 主体区域 ----
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        # 左侧面板 - 记账表单
        self._build_left_panel(main_frame)

        # 分隔线
        ttk.Separator(main_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)

        # 右侧面板
        self._build_right_panel(main_frame)

    # ================================================================
    # 左侧面板
    # ================================================================

    def _build_left_panel(self, parent):
        """构建左侧记账表单"""
        left = ttk.LabelFrame(parent, text="📝 记一笔")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # ---- 收支类型切换 ----
        ttk.Label(left, text="类型", font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 3))

        toggle_frame = ttk.Frame(left)
        toggle_frame.pack(fill=tk.X, pady=(0, 12))

        self.expense_btn = ttk.Button(
            toggle_frame, text="💸 支出", width=10,
            bootstyle="danger",
            command=lambda: self._switch_type("expense")
        )
        self.expense_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.income_btn = ttk.Button(
            toggle_frame, text="💰 收入", width=10,
            bootstyle="outline-success",
            command=lambda: self._switch_type("income")
        )
        self.income_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # ---- 金额 ----
        ttk.Label(left, text="金额（元）", font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 3))
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(left, textvariable=self.amount_var, font=('Microsoft YaHei', 10), width=22)
        self.amount_entry.pack(fill=tk.X, pady=(0, 12))
        self.amount_entry.bind('<KeyRelease>', self._on_amount_change)

        # ---- 一级分类 ----
        ttk.Label(left, text="一级分类", font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 3))
        self.l1_var = tk.StringVar()
        self.l1_combo = ttk.Combobox(
            left, textvariable=self.l1_var, font=('Microsoft YaHei', 10),
            values=list(EXPENSE_CATEGORIES.keys()), state='readonly', width=20
        )
        self.l1_combo.pack(fill=tk.X, pady=(0, 12))
        self.l1_var.trace('w', self._on_l1_change)

        # ---- 二级分类 ----
        ttk.Label(left, text="二级分类", font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 3))
        self.l2_var = tk.StringVar()
        self.l2_combo = ttk.Combobox(
            left, textvariable=self.l2_var, font=('Microsoft YaHei', 10),
            values=[], state='readonly', width=20
        )
        self.l2_combo.pack(fill=tk.X, pady=(0, 12))

        # ---- 日期 ----
        ttk.Label(left, text="日期", font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 3))
        date_frame = ttk.Frame(left)
        date_frame.pack(fill=tk.X, pady=(0, 12))

        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, font=('Microsoft YaHei', 10), width=12)
        self.date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            date_frame, text="今天", width=5, bootstyle="outline-secondary",
            command=lambda: self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        ).pack(side=tk.LEFT, padx=(5, 0))

        # ---- 备注 ----
        ttk.Label(left, text="备注（可选）", font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 3))
        self.note_var = tk.StringVar()
        self.note_entry = ttk.Entry(left, textvariable=self.note_var, font=('Microsoft YaHei', 10), width=22)
        self.note_entry.pack(fill=tk.X, pady=(0, 15))

        # ---- 按钮区 ----
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X)

        self.save_btn = ttk.Button(
            btn_frame, text="💾 保存", width=10, bootstyle="primary",
            command=self._save_record
        )
        self.save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.cancel_btn = ttk.Button(
            btn_frame, text="✖ 取消", width=10, bootstyle="outline-secondary",
            command=self._cancel_edit
        )
        self.cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.cancel_btn.configure(state=tk.DISABLED)

    # ================================================================
    # 右侧面板
    # ================================================================

    def _build_right_panel(self, parent):
        """构建右侧统计 + 列表"""
        right = ttk.Frame(parent)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # ============ 统计卡片 ============
        stats_frame = ttk.Frame(right)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # 支出卡片
        expense_card = ttk.LabelFrame(stats_frame, text="💸 本月支出")
        expense_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.stats_expense_label = ttk.Label(
            expense_card, text="¥0.00",
            font=('Microsoft YaHei', 16, 'bold'), bootstyle="danger"
        )
        self.stats_expense_label.pack()

        # 收入卡片
        income_card = ttk.LabelFrame(stats_frame, text="💰 本月收入")
        income_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.stats_income_label = ttk.Label(
            income_card, text="¥0.00",
            font=('Microsoft YaHei', 16, 'bold'), bootstyle="success"
        )
        self.stats_income_label.pack()

        # 结余卡片
        balance_card = ttk.LabelFrame(stats_frame, text="📊 本月结余")
        balance_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.stats_balance_label = ttk.Label(
            balance_card, text="¥0.00",
            font=('Microsoft YaHei', 16, 'bold'), bootstyle="info"
        )
        self.stats_balance_label.pack()

        # 笔数卡片
        count_card = ttk.LabelFrame(stats_frame, text="📋 记录数")
        count_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.stats_count_label = ttk.Label(
            count_card, text="0 笔",
            font=('Microsoft YaHei', 16, 'bold'), bootstyle="secondary"
        )
        self.stats_count_label.pack()

        # ============ 饼图 ============
        chart_frame = ttk.Frame(right)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.chart_fig = Figure(figsize=(4, 2.2), dpi=80, facecolor='#f0f0f0')
        self.chart_ax = self.chart_fig.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, master=chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ 筛选栏 ============
        filter_frame = ttk.Frame(right)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_frame, text="筛选:", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(0, 5))

        # 分类筛选
        self.filter_l1_var = tk.StringVar(value="全部分类")
        self.filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_l1_var,
            values=["全部分类"] + list(EXPENSE_CATEGORIES.keys()) + list(INCOME_CATEGORIES.keys()),
            state='readonly', width=12, font=('Microsoft YaHei', 9)
        )
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 5))

        # 日期范围
        ttk.Label(filter_frame, text="从", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(8, 3))
        self.filter_date_from = ttk.Entry(filter_frame, width=11, font=('Microsoft YaHei', 9))
        self.filter_date_from.pack(side=tk.LEFT, padx=(0, 3))
        self.filter_date_from.insert(0, datetime.now().strftime("%Y-%m-01"))

        ttk.Label(filter_frame, text="到", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(3, 3))
        self.filter_date_to = ttk.Entry(filter_frame, width=11, font=('Microsoft YaHei', 9))
        self.filter_date_to.pack(side=tk.LEFT, padx=(0, 3))
        self.filter_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Button(
            filter_frame, text="查询", width=6, bootstyle="outline-primary",
            command=self._apply_filter
        ).pack(side=tk.LEFT, padx=(5, 3))

        ttk.Button(
            filter_frame, text="显示全部", width=8, bootstyle="outline-secondary",
            command=self._reset_filter
        ).pack(side=tk.LEFT)

        # 导出按钮
        ttk.Button(
            filter_frame, text="📥 导出Excel", width=14, bootstyle="outline-success",
            command=self._export_excel
        ).pack(side=tk.RIGHT)

        # ============ 记录列表 ============
        list_frame = ttk.LabelFrame(right, text="📋 账单明细")
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('date', 'type', 'category', 'amount', 'note')
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show='headings',
            selectmode='browse', height=15
        )

        self.tree.heading('date', text='日期', command=lambda: self._sort_by('date'))
        self.tree.heading('type', text='类型')
        self.tree.heading('category', text='分类')
        self.tree.heading('amount', text='金额', command=lambda: self._sort_by('amount'))
        self.tree.heading('note', text='备注')

        self.tree.column('date', width=95, anchor=tk.CENTER)
        self.tree.column('type', width=60, anchor=tk.CENTER)
        self.tree.column('category', width=150, anchor=tk.CENTER)
        self.tree.column('amount', width=100, anchor=tk.E)
        self.tree.column('note', width=250, anchor=tk.W)

        # 行颜色标签
        self.tree.tag_configure('expense', foreground=COLOR_EXPENSE)
        self.tree.tag_configure('income', foreground=COLOR_INCOME)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击编辑
        self.tree.bind('<Double-1>', self._on_double_click)

        # 右键菜单
        self._build_context_menu()

    def _build_context_menu(self):
        """构建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="✏ 修改", command=self._edit_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑 删除", command=self._delete_selected)
        self.tree.bind('<Button-3>', self._show_context_menu)

    # ================================================================
    # 收支类型切换
    # ================================================================

    def _switch_type(self, record_type):
        """切换支出/收入模式"""
        self.record_type = record_type

        if record_type == "expense":
            self.expense_btn.configure(bootstyle="danger")
            self.income_btn.configure(bootstyle="outline-success")
            categories = EXPENSE_CATEGORIES
        else:
            self.expense_btn.configure(bootstyle="outline-danger")
            self.income_btn.configure(bootstyle="success")
            categories = INCOME_CATEGORIES

        # 更新 L1 下拉和清空选择
        self.l1_combo.configure(values=list(categories.keys()))
        self.l1_var.set('')
        self.l2_combo.configure(values=[])
        self.l2_var.set('')

    def _current_categories(self):
        """返回当前类型的分类字典"""
        return INCOME_CATEGORIES if self.record_type == "income" else EXPENSE_CATEGORIES

    # ================================================================
    # 数据加载与统计
    # ================================================================

    def _load_records(self, records=None):
        """加载记录到列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if records is None:
            records = get_all_records()

        for rec in records:
            amount_str = f"¥{rec['amount']:.2f}"
            category_str = f"{rec['category_l1']}:{rec['category_l2']}"
            type_str = "💰收入" if rec['type'] == 'income' else "💸支出"
            tag = rec['type']

            self.tree.insert('', tk.END, iid=str(rec['id']), values=(
                rec['date'],
                type_str,
                category_str,
                amount_str,
                rec['note'] or ''
            ), tags=(tag,))

        self._update_stats()

    def _update_stats(self):
        """更新统计卡片"""
        now = datetime.now()
        stats = get_monthly_stats(now.year, now.month)

        self.stats_expense_label.config(text=f"¥{stats['total_expense']:.2f}")
        self.stats_income_label.config(text=f"¥{stats['total_income']:.2f}")

        balance = stats['balance']
        if balance >= 0:
            self.stats_balance_label.config(text=f"¥{balance:.2f}", bootstyle="success")
        else:
            self.stats_balance_label.config(text=f"-¥{abs(balance):.2f}", bootstyle="danger")

        # 统计本月记录数
        month_start = f"{now.year}-{now.month:02d}-01"
        all_records = get_all_records()
        month_records = [r for r in all_records if r['date'] >= month_start]
        self.stats_count_label.config(text=f"{len(month_records)} 笔")

        # 更新饼图
        self._draw_pie_chart(stats)

    def _draw_pie_chart(self, stats):
        """绘制本月支出分类占比饼图"""
        self.chart_ax.clear()
        self.chart_ax.set_facecolor('#f0f0f0')

        expense_data = stats.get('expense_by_category', [])
        if not expense_data or stats['total_expense'] <= 0:
            self.chart_ax.text(0.5, 0.5, '本月暂无支出', ha='center', va='center',
                               fontsize=12, color='gray', transform=self.chart_ax.transAxes)
            self.chart_ax.set_xticks([])
            self.chart_ax.set_yticks([])
        else:
            labels = [d['category'] for d in expense_data]
            sizes = [d['amount'] for d in expense_data]
            colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6',
                      '#1ABC9C', '#E67E22', '#2980B9', '#C0392B', '#27AE60', '#8E44AD']

            wedges, texts, autotexts = self.chart_ax.pie(
                sizes, labels=labels, autopct='%1.1f%%',
                colors=colors[:len(labels)],
                startangle=90, pctdistance=0.75,
                textprops={'fontsize': 8}
            )
            for t in autotexts:
                t.set_fontsize(7)
                t.set_color('white')

        self.chart_fig.tight_layout(pad=0.5)
        self.chart_canvas.draw()

    # ================================================================
    # 表单交互
    # ================================================================

    def _on_l1_change(self, *args):
        """一级分类变化时，更新二级分类选项"""
        l1 = self.l1_var.get()
        categories = self._current_categories()
        if l1 in categories:
            self.l2_combo.configure(values=categories[l1])
            self.l2_var.set('')
        else:
            self.l2_combo.configure(values=[])
            self.l2_var.set('')

    def _on_amount_change(self, event=None):
        """金额输入时，限制只能输入数字和小数点"""
        val = self.amount_var.get()
        filtered = ''.join(c for c in val if c.isdigit() or c == '.')
        if filtered.count('.') > 1:
            parts = filtered.split('.')
            filtered = parts[0] + '.' + ''.join(parts[1:])
        if '.' in filtered:
            int_part, dec_part = filtered.split('.', 1)
            dec_part = dec_part[:2]
            filtered = int_part + '.' + dec_part
        if filtered != val:
            self.amount_var.set(filtered)
            self.amount_entry.icursor(len(filtered))

    def _clear_form(self):
        """清空表单"""
        self.record_type = "expense"
        self._switch_type("expense")
        self.amount_var.set('')
        self.l1_var.set('')
        self.l2_combo.configure(values=[])
        self.l2_var.set('')
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.note_var.set('')
        self.editing_id = None
        self.save_btn.configure(text="💾 保存", bootstyle="primary")
        self.cancel_btn.configure(state=tk.DISABLED)

    def _cancel_edit(self):
        self._clear_form()

    # ================================================================
    # 保存 / 编辑 / 删除
    # ================================================================

    def _save_record(self):
        """保存一条记录（新建或修改）"""
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                self._show_warning("金额必须大于 0")
                return
        except ValueError:
            self._show_warning("请输入有效的金额数字")
            return

        category_l1 = self.l1_var.get()
        if not category_l1:
            self._show_warning("请选择一级分类")
            return

        category_l2 = self.l2_var.get()
        if not category_l2:
            self._show_warning("请选择二级分类")
            return

        date = self.date_var.get().strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            self._show_warning("日期格式不正确，请使用 YYYY-MM-DD 格式\n如：2026-07-16")
            return

        note = self.note_var.get().strip()

        if self.editing_id:
            update_record(self.editing_id, amount, category_l1, category_l2, date, note, self.record_type)
        else:
            add_record(amount, category_l1, category_l2, date, note, self.record_type)

        self._clear_form()
        self._load_records()

    def _show_warning(self, msg):
        """显示警告弹窗"""
        from tkinter import messagebox
        messagebox.showwarning("提示", msg)

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            from tkinter import messagebox
            messagebox.showinfo("提示", "请先在列表中选中一条记录")
            return

        from tkinter import messagebox
        record = self.tree.item(selected[0])
        confirm = messagebox.askyesno(
            "确认删除",
            f"确定要删除这条记录吗？\n\n"
            f"日期：{record['values'][0]}\n"
            f"类型：{record['values'][1]}\n"
            f"分类：{record['values'][2]}\n"
            f"金额：{record['values'][3]}"
        )
        if confirm:
            record_id = int(selected[0])
            delete_record(record_id)
            if self.editing_id == record_id:
                self._clear_form()
            self._load_records()

    def _edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            from tkinter import messagebox
            messagebox.showinfo("提示", "请先在列表中选中一条记录")
            return

        record_id = int(selected[0])
        records = get_all_records()
        record = next((r for r in records if r['id'] == record_id), None)
        if not record:
            return

        # 设置类型
        self.record_type = record.get('type', 'expense')
        self._switch_type(self.record_type)

        # 填入表单
        self.amount_var.set(str(record['amount']))
        self.l1_var.set(record['category_l1'])
        self._on_l1_change()
        self.l2_var.set(record['category_l2'])
        self.date_var.set(record['date'])
        self.note_var.set(record['note'] or '')

        self.editing_id = record_id
        self.save_btn.configure(text="✏ 更新", bootstyle="warning")
        self.cancel_btn.configure(state=tk.NORMAL)

    # ================================================================
    # 事件处理
    # ================================================================

    def _on_double_click(self, event):
        self._edit_selected()

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _apply_filter(self):
        category = self.filter_l1_var.get()
        date_from = self.filter_date_from.get().strip()
        date_to = self.filter_date_to.get().strip()

        # 按分类筛选
        all_expense_keys = list(EXPENSE_CATEGORIES.keys())
        all_income_keys = list(INCOME_CATEGORIES.keys())

        if category and category != "全部分类":
            if category in all_expense_keys:
                records = get_records_by_category(category, record_type="expense")
            elif category in all_income_keys:
                records = get_records_by_category(category, record_type="income")
            else:
                records = get_all_records()
        else:
            records = get_all_records()

        # 日期过滤
        if date_from:
            records = [r for r in records if r['date'] >= date_from]
        if date_to:
            records = [r for r in records if r['date'] <= date_to]

        self._load_records(records)

    def _reset_filter(self):
        self.filter_l1_var.set("全部分类")
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_from.insert(0, datetime.now().strftime("%Y-%m-01"))
        self.filter_date_to.delete(0, tk.END)
        self.filter_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._load_records()

    def _sort_by(self, column):
        records = get_all_records()
        if column == 'amount':
            records.sort(key=lambda r: r['amount'])
        else:
            records.sort(key=lambda r: r['date'])
        self._load_records(records)

    # ================================================================
    # 导出
    # ================================================================

    def _export_excel(self):
        from utils.export import export_to_excel
        from tkinter import messagebox
        records = get_all_records()
        if not records:
            messagebox.showinfo("提示", "没有可导出的记录")
            return
        filepath = export_to_excel(records)
        messagebox.showinfo("导出成功", f"已导出到：\n{filepath}")
