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
from matplotlib import cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import (
    init_db, get_categories, get_all_category_l1,
    add_category, update_category_name, delete_category, is_preset_category,
    add_record, get_all_records, get_record_by_id, update_record, delete_record,
    get_records_by_date_range, get_records_by_category, get_monthly_stats,
    format_display, parse_display
)
from ui.snake_game import SnakeGame

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

        # 贪吃蛇游戏（延迟构建，节约启动资源）
        self.snake_game = None

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

        # 贪吃蛇入口
        ttk.Button(
            title_bar, text="🐍 贪吃蛇", width=12, bootstyle="outline-warning",
            command=self._show_snake_game
        ).pack(side=tk.RIGHT)

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
            values=[format_display(x) for x in get_all_category_l1('expense')],
            state='readonly', width=20
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
        self.l2_combo.pack(fill=tk.X, pady=(0, 8))

        # ---- 管理分类 ----
        ttk.Button(
            left, text="⚙ 管理分类", width=12, bootstyle="outline-secondary",
            command=self._open_category_manager
        ).pack(anchor=tk.W, pady=(0, 12))

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
        self.right_panel = ttk.Frame(parent)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # ---- 记账功能容器（统计 + 筛选 + 列表）----
        self.right_accounting = ttk.Frame(self.right_panel)
        self.right_accounting.pack(fill=tk.BOTH, expand=True)

        # ============ 统计卡片 ============
        stats_frame = ttk.Frame(self.right_accounting)
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
        chart_frame = ttk.Frame(self.right_accounting)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.chart_fig = Figure(figsize=(4, 2.2), dpi=80, facecolor='#f0f0f0')
        self.chart_ax = self.chart_fig.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, master=chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ 筛选栏 ============
        filter_frame = ttk.Frame(self.right_accounting)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_frame, text="筛选:", font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(0, 5))

        # 分类筛选
        self.filter_l1_var = tk.StringVar(value="全部分类")
        all_l1 = [format_display(x) for x in
                  get_all_category_l1('expense') + get_all_category_l1('income')]
        self.filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_l1_var,
            values=["全部分类"] + all_l1,
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
        list_frame = ttk.LabelFrame(self.right_accounting, text="📋 账单明细")
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
    # 记账 / 贪吃蛇 切换
    # ================================================================

    def _show_snake_game(self):
        """切换到贪吃蛇游戏（首次调用时延迟构建）"""
        if self.snake_game is None:
            self.snake_game = SnakeGame(
                self.right_panel, on_back=self._show_accounting
            )
        self.right_accounting.pack_forget()
        self.snake_game.pack(fill=tk.BOTH, expand=True)
        self.snake_game.activate()

    def _show_accounting(self):
        """切换回记账界面"""
        if self.snake_game is not None:
            self.snake_game.deactivate()
            self.snake_game.pack_forget()
        self.right_accounting.pack(fill=tk.BOTH, expand=True)

    # ================================================================
    # 收支类型切换
    # ================================================================

    def _switch_type(self, record_type):
        """切换支出/收入模式"""
        self.record_type = record_type

        if record_type == "expense":
            self.expense_btn.configure(bootstyle="danger")
            self.income_btn.configure(bootstyle="outline-success")
        else:
            self.expense_btn.configure(bootstyle="outline-danger")
            self.income_btn.configure(bootstyle="success")

        # 从数据库读取最新分类，更新下拉框
        self.l1_combo.configure(values=[format_display(x) for x in get_all_category_l1(record_type)])
        self.l1_var.set('')
        self.l2_combo.configure(values=[])
        self.l2_var.set('')

    def _current_categories(self):
        """返回当前类型的分类字典（从数据库读取）"""
        return get_categories(self.record_type)

    def _refresh_category_dropdowns(self):
        """分类管理操作后，刷新主窗口所有分类相关下拉框。"""
        self.l1_combo.configure(values=[format_display(x) for x in get_all_category_l1(self.record_type)])
        self._on_l1_change()
        # 刷新筛选下拉框
        all_l1 = get_all_category_l1('expense') + get_all_category_l1('income')
        self.filter_combo.configure(values=["全部分类"] + [format_display(x) for x in all_l1])

    # ================================================================
    # 管理分类弹窗
    # ================================================================

    def _open_category_manager(self):
        """打开管理分类弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title("管理分类")
        dialog.geometry("680x520")
        dialog.transient(self.root)
        dialog.grab_set()

        # 当前查看的类型
        view_type = tk.StringVar(value="expense")
        # 当前选中的分类信息
        selected_info = {"l1": None, "l2": None, "is_l1": False, "is_preset": True}

        # ============ 左侧：类型切换 + 分类树 ============
        left_frame = ttk.Frame(dialog)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 5), pady=15)

        # 类型切换按钮
        toggle_frame = ttk.Frame(left_frame)
        toggle_frame.pack(fill=tk.X, pady=(0, 8))

        def on_type_switch(t):
            view_type.set(t)
            load_tree(t)
            update_new_l1_combo()
            _update_toggle_style()
            # 清空选中
            selected_info.update({"l1": None, "l2": None, "is_l1": False, "is_preset": True})
            update_info_panel()

        def _update_toggle_style():
            """刷新切换按钮的高亮状态"""
            for child in toggle_frame.winfo_children():
                child.destroy()
            vt = view_type.get()
            ttk.Button(
                toggle_frame, text="💸 支出分类", width=12,
                bootstyle="danger" if vt == "expense" else "outline-danger",
                command=lambda: on_type_switch("expense")
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(
                toggle_frame, text="💰 收入分类", width=12,
                bootstyle="success" if vt == "income" else "outline-success",
                command=lambda: on_type_switch("income")
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # 首次创建切换按钮
        _update_toggle_style()

        # Treeview 分类树
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(tree_frame, columns=(), show='tree', selectmode='browse')
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tree.tag_configure('preset', foreground='gray')
        tree.tag_configure('custom', foreground='black')

        def load_tree(cat_type):
            tree.delete(*tree.get_children())
            categories = get_categories(cat_type)
            for l1, l2_list in categories.items():
                # 检查该 L1 是否有预置项
                has_preset = any(
                    is_preset_category(cat_type, l1, l2) for l2 in l2_list
                )
                l1_tag = 'preset' if has_preset else 'custom'
                l1_iid = tree.insert('', tk.END, text=format_display(l1), open=True, tags=(l1_tag,))
                for l2 in l2_list:
                    is_p = is_preset_category(cat_type, l1, l2)
                    l2_tag = 'preset' if is_p else 'custom'
                    tree.insert(l1_iid, tk.END, text=format_display(l2), tags=(l2_tag,))

        # ============ 右侧：信息 + 操作 ============
        right_frame = ttk.Frame(dialog, width=280)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 15), pady=15)
        right_frame.pack_propagate(False)

        # 选中信息
        info_frame = ttk.LabelFrame(right_frame, text="选中分类")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_name_label = ttk.Label(info_frame, text="名称：未选中", font=('Microsoft YaHei', 10))
        info_name_label.pack(anchor=tk.W, pady=(5, 2), padx=10)

        info_source_label = ttk.Label(info_frame, text="", font=('Microsoft YaHei', 9))
        info_source_label.pack(anchor=tk.W, pady=(0, 5), padx=10)

        def update_info_panel():
            l1 = selected_info.get("l1")
            l2 = selected_info.get("l2")
            is_l1 = selected_info.get("is_l1")
            is_p = selected_info.get("is_preset", True)

            if l1 is None:
                info_name_label.config(text="名称：未选中")
                info_source_label.config(text="")
                rename_btn.config(state=tk.DISABLED)
                delete_btn.config(state=tk.DISABLED)
                return

            if is_l1:
                info_name_label.config(text=f"名称：{format_display(l1)}（一级分类）")
            else:
                info_name_label.config(text=f"名称：{format_display(l1)} : {format_display(l2)}")

            if is_p:
                info_source_label.config(text="来源：预置分类（不可修改）", foreground='gray')
            else:
                info_source_label.config(text="来源：用户自定义", foreground='#27AE60')

            # 根据是否预设来启用/禁用按钮
            if is_p:
                rename_btn.config(state=tk.DISABLED)
                delete_btn.config(state=tk.DISABLED)
            else:
                rename_btn.config(state=tk.NORMAL)
                delete_btn.config(state=tk.NORMAL)

        # 操作按钮
        action_frame = ttk.LabelFrame(right_frame, text="操作")
        action_frame.pack(fill=tk.X, pady=(0, 10))

        def do_rename():
            l1 = selected_info.get("l1")
            l2 = selected_info.get("l2")
            is_l1 = selected_info.get("is_l1")
            if not l1:
                return
            ct = view_type.get()

            if is_l1:
                # 修改一级分类名：弹出简单输入框
                from tkinter import simpledialog
                new_name = simpledialog.askstring(
                    "修改一级分类", f"将一级分类「{l1}」重命名为：",
                    parent=dialog, initialvalue=l1
                )
                if not new_name or new_name.strip() == l1:
                    return
                # 修改该 L1 下所有用户自定义的 L2 行
                categories = get_categories(ct)
                for old_l2 in categories.get(l1, []):
                    if not is_preset_category(ct, l1, old_l2):
                        success, msg = update_category_name(ct, l1, old_l2, new_name.strip(), old_l2)
                        if not success:
                            from tkinter import messagebox
                            messagebox.showwarning("修改失败", msg, parent=dialog)
                            return
            else:
                # 修改二级分类名
                from tkinter import simpledialog
                new_name = simpledialog.askstring(
                    "修改二级分类", f"将二级分类「{l2}」重命名为：",
                    parent=dialog, initialvalue=l2
                )
                if not new_name or new_name.strip() == l2:
                    return
                success, msg = update_category_name(ct, l1, l2, l1, new_name.strip())
                if not success:
                    from tkinter import messagebox
                    messagebox.showwarning("修改失败", msg, parent=dialog)
                    return

            load_tree(ct)
            update_info_panel()
            self._refresh_category_dropdowns()

        rename_btn = ttk.Button(
            action_frame, text="✏ 修改名称", width=14,
            bootstyle="outline-primary",
            command=do_rename
        )
        rename_btn.pack(fill=tk.X, pady=(5, 3), padx=10)

        def do_delete():
            l1 = selected_info.get("l1")
            l2 = selected_info.get("l2")
            is_l1 = selected_info.get("is_l1")
            if not l1:
                return
            ct = view_type.get()

            from tkinter import messagebox

            if is_l1:
                # 删除整个一级分类（仅用户自定义的 L2）
                categories = get_categories(ct)
                l2_list = categories.get(l1, [])
                user_l2s = [x for x in l2_list if not is_preset_category(ct, l1, x)]
                if not user_l2s:
                    messagebox.showwarning("提示", "该一级分类下没有可删除的自定义分类", parent=dialog)
                    return
                # 检查每个 L2 是否有记录
                for old_l2 in user_l2s:
                    success, msg = delete_category(ct, l1, old_l2)
                    if not success:
                        messagebox.showwarning("删除失败", f"「{l1}:{old_l2}」{msg}", parent=dialog)
                        load_tree(ct)
                        update_info_panel()
                        return

                confirm = messagebox.askyesno(
                    "确认删除",
                    f"确定要删除一级分类「{l1}」下的所有自定义二级分类吗？\n共 {len(user_l2s)} 个。",
                    parent=dialog
                )
                if not confirm:
                    return
                for old_l2 in user_l2s:
                    delete_category(ct, l1, old_l2)  # 第二次调用直接删
            else:
                confirm = messagebox.askyesno(
                    "确认删除",
                    f"确定要删除分类「{l1}:{l2}」吗？",
                    parent=dialog
                )
                if not confirm:
                    return
                success, msg = delete_category(ct, l1, l2)
                if not success:
                    messagebox.showwarning("删除失败", msg, parent=dialog)
                    return

            selected_info.update({"l1": None, "l2": None, "is_l1": False, "is_preset": True})
            load_tree(ct)
            update_info_panel()
            self._refresh_category_dropdowns()

        delete_btn = ttk.Button(
            action_frame, text="🗑 删除分类", width=14,
            bootstyle="outline-danger",
            command=do_delete
        )
        delete_btn.pack(fill=tk.X, pady=(3, 5), padx=10)

        # 新增分类
        add_frame = ttk.LabelFrame(right_frame, text="新增分类")
        add_frame.pack(fill=tk.X)

        ttk.Label(add_frame, text="一级分类（可选已有或输入新建）", font=('Microsoft YaHei', 9)).pack(
            anchor=tk.W, padx=10, pady=(5, 2))
        new_l1_var = tk.StringVar()
        new_l1_combo = ttk.Combobox(
            add_frame, textvariable=new_l1_var, font=('Microsoft YaHei', 10),
            state='normal', width=18
        )
        new_l1_combo.pack(fill=tk.X, padx=10, pady=(0, 5))

        def update_new_l1_combo():
            new_l1_combo.configure(values=[format_display(x) for x in get_all_category_l1(view_type.get())])

        ttk.Label(add_frame, text="二级分类", font=('Microsoft YaHei', 9)).pack(
            anchor=tk.W, padx=10, pady=(0, 2))
        new_l2_var = tk.StringVar()
        new_l2_entry = ttk.Entry(add_frame, textvariable=new_l2_var, font=('Microsoft YaHei', 10), width=18)
        new_l2_entry.pack(fill=tk.X, padx=10, pady=(0, 8))

        def do_add():
            l1 = parse_display(new_l1_var.get()).strip()
            l2 = new_l2_var.get().strip()
            if not l1:
                from tkinter import messagebox
                messagebox.showwarning("提示", "请输入或选择一级分类", parent=dialog)
                return
            if not l2:
                from tkinter import messagebox
                messagebox.showwarning("提示", "请输入二级分类名称", parent=dialog)
                return

            ct = view_type.get()
            success, msg = add_category(ct, l1, l2)
            if not success:
                from tkinter import messagebox
                messagebox.showwarning("新增失败", msg, parent=dialog)
                return

            new_l2_var.set('')
            load_tree(ct)
            update_new_l1_combo()
            self._refresh_category_dropdowns()

        ttk.Button(
            add_frame, text="➕ 新增", width=14,
            bootstyle="success",
            command=do_add
        ).pack(fill=tk.X, padx=10, pady=(0, 8))

        # 树选中事件
        def on_tree_select(event):
            sel = tree.selection()
            if not sel:
                selected_info.update({"l1": None, "l2": None, "is_l1": False, "is_preset": True})
                update_info_panel()
                return

            item = tree.item(sel[0])
            parent = tree.parent(sel[0])
            ct = view_type.get()

            if parent == '':
                # 选中的是一级分类节点
                l1 = parse_display(item['text'])
                is_l1 = True
                l2 = None
                # 检查该 L1 下是否全是预设
                cats = get_categories(ct)
                l2_list = cats.get(l1, [])
                all_preset = all(is_preset_category(ct, l1, x) for x in l2_list) if l2_list else True
                selected_info.update({"l1": l1, "l2": None, "is_l1": True, "is_preset": all_preset})
            else:
                # 选中的是二级分类节点
                l1 = parse_display(tree.item(parent)['text'])
                l2 = parse_display(item['text'])
                is_p = is_preset_category(ct, l1, l2)
                selected_info.update({"l1": l1, "l2": l2, "is_l1": False, "is_preset": is_p})

            update_info_panel()

        tree.bind('<<TreeviewSelect>>', on_tree_select)

        # 初始加载
        load_tree("expense")
        update_new_l1_combo()
        update_info_panel()

    # ================================================================
    # 数据加载与统计
    # ================================================================

    def _load_records(self, records=None):
        """加载记录到列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if records is None:
            records = get_all_records()

        # 缓存当前显示的记录，供 _sort_by 使用
        self._current_records = records

        for rec in records:
            amount_str = f"¥{rec['amount']:.2f}"
            category_str = f"{format_display(rec['category_l1'])}:{format_display(rec['category_l2'])}"
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
            total = sum(d['amount'] for d in expense_data)

            # 占比 < 2% 的小分类合并为"其他小分类"，避免标签堆叠看不清
            threshold = 0.02
            main_data = []
            other_amount = 0
            for d in expense_data:
                pct = d['amount'] / total if total > 0 else 0
                if pct >= threshold:
                    main_data.append(d)
                else:
                    other_amount += d['amount']

            if other_amount > 0:
                main_data.append({'category': '其他小分类', 'amount': other_amount})

            # 标签加 emoji
            labels = [format_display(d['category']) for d in main_data]
            sizes = [d['amount'] for d in main_data]

            # 用 colormap 自动生成颜色
            color_norm = len(labels) if len(labels) > 1 else 2
            colors = [cm.Set3(i / color_norm) for i in range(len(labels))]

            # <1% 的显示为 "<1%" 而不是 "0.0%"
            def autopct(pct):
                return '<1%' if pct < 1 else f'{pct:.1f}%'

            wedges, texts, autotexts = self.chart_ax.pie(
                sizes, labels=labels, autopct=autopct,
                colors=colors,
                startangle=90, pctdistance=0.75,
                textprops={'fontsize': 8}
            )
            # Set3 是浅色系，用深色文字更可读
            for t in autotexts:
                t.set_fontsize(7)
                t.set_color('#333333')

        self.chart_fig.tight_layout(pad=0.5)
        self.chart_canvas.draw()

    # ================================================================
    # 表单交互
    # ================================================================

    def _on_l1_change(self, *args):
        """一级分类变化时，更新二级分类选项"""
        l1 = parse_display(self.l1_var.get())
        categories = self._current_categories()
        if l1 in categories:
            self.l2_combo.configure(values=[format_display(x) for x in categories[l1]])
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

        category_l1 = parse_display(self.l1_var.get())
        if not category_l1:
            self._show_warning("请选择一级分类")
            return

        category_l2 = parse_display(self.l2_var.get())
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
        record = get_record_by_id(record_id)
        if not record:
            return

        # 设置类型
        self.record_type = record.get('type', 'expense')
        self._switch_type(self.record_type)

        # 填入表单
        self.amount_var.set(str(record['amount']))
        self.l1_var.set(format_display(record['category_l1']))
        self._on_l1_change()
        self.l2_var.set(format_display(record['category_l2']))
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
        category = parse_display(self.filter_l1_var.get())
        date_from = self.filter_date_from.get().strip()
        date_to = self.filter_date_to.get().strip()

        # 按分类筛选
        all_expense_keys = get_all_category_l1('expense')
        all_income_keys = get_all_category_l1('income')

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
        # 刷新筛选下拉框（含用户新增的分类）
        all_l1 = get_all_category_l1('expense') + get_all_category_l1('income')
        self.filter_combo.configure(values=["全部分类"] + [format_display(x) for x in all_l1])
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_from.insert(0, datetime.now().strftime("%Y-%m-01"))
        self.filter_date_to.delete(0, tk.END)
        self.filter_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._load_records()

    def _sort_by(self, column):
        # 对当前已缓存的记录排序（保留筛选状态）
        records = getattr(self, '_current_records', None) or get_all_records()
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
