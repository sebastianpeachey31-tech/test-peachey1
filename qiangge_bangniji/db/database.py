"""
数据库模块 - 管理 SQLite 数据库的创建、连接和操作。
"""
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

# 数据库文件路径（存在项目 data 目录下）
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'qiangge.db')

# ============================================================
# 支出分类（一级分类 -> 二级分类列表）
# ============================================================
EXPENSE_CATEGORIES = {
    "餐饮": ["早餐", "午餐", "晚餐", "零食饮料", "水果", "聚餐请客", "外卖配送费"],
    "交通": ["公交地铁", "出租车/网约车", "火车高铁", "飞机", "加油/充电", "停车费", "共享单车"],
    "购物": ["日用品", "数码电器", "家居家具", "书本文具", "宠物用品", "其他购物"],
    "居住": ["房租/房贷", "水费", "电费", "燃气费", "物业费", "维修/装修", "日租/酒店"],
    "娱乐": ["游戏充值", "电影演出", "旅游度假", "运动健身", "KTV/酒吧", "视频会员", "彩票"],
    "服饰": ["衣服", "鞋子", "包包", "配饰", "美容美发", "化妆品"],
    "医疗": ["挂号/门诊", "药品", "住院", "体检", "牙科", "保健品"],
    "通讯": ["手机话费", "宽带网费", "快递邮寄"],
    "教育": ["培训课程", "书籍资料", "考试报名", "文具耗材", "儿童教育"],
    "人情": ["红包/礼金", "请客送礼", "慈善捐款", "孝敬父母"],
    "其他": ["日常杂项", "忘记分类"],
}

# ============================================================
# 收入分类（一级分类 -> 二级分类列表）
# ============================================================
INCOME_CATEGORIES = {
    "工资收入": ["月薪", "奖金", "补贴", "加班费"],
    "投资收益": ["理财收益", "股票收益", "房租收入", "其他投资"],
    "兼职副业": ["副业收入", "稿费", "咨询费"],
    "人情往来": ["红包收入", "礼金收入", "还款收回"],
    "其他收入": ["退款报销", "意外之财", "其他"],
}


# ============================================================
# 分类图标（emoji 表情映射）
# ============================================================
CATEGORY_ICON = {
    # --- 支出一级分类 ---
    "餐饮": "🍽️", "交通": "🚗", "购物": "🛒", "居住": "🏠",
    "娱乐": "🎮", "服饰": "👗", "医疗": "🏥", "通讯": "📱",
    "教育": "📚", "人情": "🎁", "其他": "📦",
    # --- 收入一级分类 ---
    "工资收入": "💰", "投资收益": "📈", "兼职副业": "💼",
    "人情往来": "🎀", "其他收入": "💵",
    # --- 支出二级分类 ---
    "早餐": "🥐", "午餐": "🍱", "晚餐": "🍲",
    "零食饮料": "🧃", "水果": "🍎", "聚餐请客": "🥂", "外卖配送费": "🛵",
    "公交地铁": "🚇", "出租车/网约车": "🚕", "火车高铁": "🚄",
    "飞机": "✈️", "加油/充电": "⛽", "停车费": "🅿️", "共享单车": "🚲",
    "日用品": "🧹", "数码电器": "💻", "家居家具": "🛋️",
    "书本文具": "✏️", "宠物用品": "🐾", "其他购物": "🛍️",
    "房租/房贷": "🏡", "水费": "💧", "电费": "⚡",
    "燃气费": "🔥", "物业费": "🏢", "维修/装修": "🔧", "日租/酒店": "🏨",
    "游戏充值": "🎮", "电影演出": "🎬", "旅游度假": "🏖️",
    "运动健身": "🏋️", "KTV/酒吧": "🎤", "视频会员": "📺", "彩票": "🎫",
    "衣服": "👕", "鞋子": "👟", "包包": "👜",
    "配饰": "💍", "美容美发": "💇", "化妆品": "💄",
    "挂号/门诊": "🩺", "药品": "💊", "住院": "🏥",
    "体检": "🩻", "牙科": "🦷", "保健品": "💪",
    "手机话费": "📞", "宽带网费": "🌐", "快递邮寄": "📦",
    "培训课程": "🎓", "书籍资料": "📖", "考试报名": "📝",
    "文具耗材": "🖊️", "儿童教育": "👶",
    "红包/礼金": "🧧", "请客送礼": "🎁", "慈善捐款": "🤝", "孝敬父母": "👴",
    "日常杂项": "📌", "忘记分类": "❓",
    # --- 收入二级分类 ---
    "月薪": "💰", "奖金": "🏆", "补贴": "📋", "加班费": "⏰",
    "理财收益": "📊", "股票收益": "📈", "房租收入": "🏠", "其他投资": "💎",
    "副业收入": "🔧", "稿费": "✍️", "咨询费": "💬",
    "红包收入": "🧧", "礼金收入": "🎀", "还款收回": "💳",
    "退款报销": "↩️", "意外之财": "🍀",
}


def format_display(category_name):
    """将分类名格式化为带 emoji 的显示名称，如 '🍽️ 餐饮'"""
    icon = CATEGORY_ICON.get(category_name, "📌")
    return f"{icon} {category_name}"


def parse_display(display_text):
    """从带 emoji 的显示名称中提取原始分类名，如 '🍽️ 餐饮' -> '餐饮'

    format_display 的格式是固定的：'{emoji} {name}'，emoji 和名称之间
    有一个空格。所以只需要按空格分割并取后半部分即可。
    不依赖 Unicode 范围判断，兼容所有语言字符。
    """
    parts = display_text.split(' ', 1)
    return parts[1] if len(parts) > 1 else display_text


def get_connection():
    """获取数据库连接。如果目录不存在则自动创建。"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以用列名访问
    return conn


@contextmanager
def get_db():
    """数据库连接的上下文管理器，自动关闭连接，即使中途出错也不会泄露。

    用法（替代原来手写 conn.close() 的方式）：
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
            ...
        # 出了 with 块，连接自动关闭，不用手动 conn.close()
        # 就算中间抛了异常，连接也会被正确关闭
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库：创建表结构，如果有旧版表则自动升级。"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL NOT NULL,
                type        TEXT NOT NULL DEFAULT 'expense',
                category_l1 TEXT NOT NULL,
                category_l2 TEXT NOT NULL,
                note        TEXT DEFAULT '',
                date        TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        ''')

        # 兼容旧表：如果之前创建的表没有 type 列，自动加上
        # PRAGMA 是 SQLite 的"查户口"命令，table_info 可以查出表里有哪些列
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'type' not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN type TEXT NOT NULL DEFAULT 'expense'")

        # 分类管理表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT NOT NULL,
                category_l1 TEXT NOT NULL,
                category_l2 TEXT NOT NULL,
                is_preset   INTEGER NOT NULL DEFAULT 0,
                sort_order  INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        ''')

        conn.commit()

    # 首次启动时写入预置分类种子数据
    _seed_preset_categories()


def _seed_preset_categories():
    """首次运行时将硬编码的预置分类写入 categories 表。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as cnt FROM categories')
        if cursor.fetchone()['cnt'] > 0:
            return

        sort = 0
        for l1, l2_list in EXPENSE_CATEGORIES.items():
            for l2 in l2_list:
                cursor.execute(
                    'INSERT INTO categories (type, category_l1, category_l2, is_preset, sort_order) '
                    'VALUES (?, ?, ?, 1, ?)',
                    ('expense', l1, l2, sort)
                )
                sort += 1

        sort = 0
        for l1, l2_list in INCOME_CATEGORIES.items():
            for l2 in l2_list:
                cursor.execute(
                    'INSERT INTO categories (type, category_l1, category_l2, is_preset, sort_order) '
                    'VALUES (?, ?, ?, 1, ?)',
                    ('income', l1, l2, sort)
                )
                sort += 1

        conn.commit()


# ============================================================
# 分类管理：查询、新增、改名、删除
# ============================================================

def get_categories(cat_type):
    """返回指定类型的分类字典 {一级分类: [二级分类列表]}，按 sort_order 排序。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT category_l1, category_l2 FROM categories '
            'WHERE type = ? ORDER BY sort_order',
            (cat_type,)
        )
        rows = cursor.fetchall()

    result = {}
    for row in rows:
        l1 = row['category_l1']
        if l1 not in result:
            result[l1] = []
        result[l1].append(row['category_l2'])
    return result


def get_all_category_l1(cat_type):
    """返回指定类型的所有一级分类名称列表（用于下拉框）。"""
    categories = get_categories(cat_type)
    return list(categories.keys())


def is_preset_category(cat_type, category_l1, category_l2):
    """查询某个分类是否为预置分类。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT is_preset FROM categories '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (cat_type, category_l1, category_l2)
        )
        row = cursor.fetchone()
    return bool(row['is_preset']) if row else False


def add_category(cat_type, category_l1, category_l2):
    """新增一个用户自定义分类（is_preset=0）。返回 (True, None) 或 (False, 错误原因)。"""
    # 不允许空名称
    if not category_l1.strip() or not category_l2.strip():
        return False, "分类名称不能为空"

    with get_db() as conn:
        cursor = conn.cursor()

        # 检查是否重复
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM categories '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (cat_type, category_l1.strip(), category_l2.strip())
        )
        if cursor.fetchone()['cnt'] > 0:
            return False, "该分类已存在"

        # 获取该一级分类下的最大 sort_order
        cursor.execute(
            'SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order FROM categories '
            'WHERE type = ? AND category_l1 = ?',
            (cat_type, category_l1.strip())
        )
        next_order = cursor.fetchone()['next_order']

        cursor.execute(
            'INSERT INTO categories (type, category_l1, category_l2, is_preset, sort_order) '
            'VALUES (?, ?, ?, 0, ?)',
            (cat_type, category_l1.strip(), category_l2.strip(), next_order)
        )
        conn.commit()
    return True, None


def update_category_name(cat_type, old_l1, old_l2, new_l1, new_l2):
    """
    修改分类名称。只允许改 is_preset=0 的分类。
    同时同步更新 expenses 表中所有匹配记录。
    返回 (True, None) 或 (False, 错误原因)。
    """
    new_l1 = new_l1.strip()
    new_l2 = new_l2.strip()
    if not new_l1 or not new_l2:
        return False, "分类名称不能为空"

    with get_db() as conn:
        cursor = conn.cursor()

        # 验证是用户自定义分类
        cursor.execute(
            'SELECT is_preset FROM categories '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (cat_type, old_l1, old_l2)
        )
        row = cursor.fetchone()
        if not row:
            return False, "分类不存在"
        if row['is_preset']:
            return False, "预置分类不可修改"

        # 检查新名称是否与已有分类重复
        if old_l1 != new_l1 or old_l2 != new_l2:
            cursor.execute(
                'SELECT COUNT(*) as cnt FROM categories '
                'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
                (cat_type, new_l1, new_l2)
            )
            if cursor.fetchone()['cnt'] > 0:
                return False, "新名称与已有分类重复"

        # 更新 categories 表
        cursor.execute(
            'UPDATE categories SET category_l1 = ?, category_l2 = ? '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ? AND is_preset = 0',
            (new_l1, new_l2, cat_type, old_l1, old_l2)
        )

        # 同步更新 expenses 表
        cursor.execute(
            'UPDATE expenses SET category_l1 = ?, category_l2 = ? '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (new_l1, new_l2, cat_type, old_l1, old_l2)
        )

        conn.commit()
    return True, None


def delete_category(cat_type, category_l1, category_l2):
    """
    删除用户自定义分类（is_preset=0）。
    如果有 expenses 记录在用则拒绝删除。
    返回 (True, None) 或 (False, 错误原因)。
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # 验证是用户自定义分类
        cursor.execute(
            'SELECT is_preset FROM categories '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (cat_type, category_l1, category_l2)
        )
        row = cursor.fetchone()
        if not row:
            return False, "分类不存在"
        if row['is_preset']:
            return False, "预置分类不可删除"

        # 检查是否有记录在使用
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM expenses '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (cat_type, category_l1, category_l2)
        )
        count = cursor.fetchone()['cnt']
        if count > 0:
            return False, f"该分类被 {count} 条记录使用，请先修改这些记录后再删除"

        cursor.execute(
            'DELETE FROM categories '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ? AND is_preset = 0',
            (cat_type, category_l1, category_l2)
        )
        conn.commit()
    return True, None


# ============================================================
# CRUD 操作：增删改查
# ============================================================

def add_record(amount, category_l1, category_l2, date, note="", record_type="expense"):
    """添加一条记录（支出或收入）。

    参数：
        amount: 金额（元），比如 25.50
        category_l1: 一级分类，如"餐饮"
        category_l2: 二级分类，如"午餐"
        date: 日期，格式 "2026-07-25"
        note: 备注（可选），比如"食堂二楼麻辣烫"
        record_type: "expense"=支出 或 "income"=收入

    返回：
        新记录的 ID 编号（整数）
    """
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO expenses (amount, type, category_l1, category_l2, note, date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (amount, record_type, category_l1, category_l2, note, date, now, now))
        conn.commit()
        record_id = cursor.lastrowid
    return record_id


def get_all_records(order="date DESC"):
    """获取所有记录，默认按日期倒序。"""
    # 只允许安全的排序字段，防 SQL 注入（白名单校验）
    # 如果传入不在白名单中的值，直接抛出异常，不执行 SQL
    ALLOWED_ORDERS = {"date ASC", "date DESC", "amount ASC", "amount DESC"}
    if order not in ALLOWED_ORDERS:
        raise ValueError(f"无效的排序参数: {order}")
    with get_db() as conn:
        cursor = conn.cursor()
        # order 已经过白名单校验，安全拼接
        cursor.execute(f'SELECT * FROM expenses ORDER BY {order}')
        rows = cursor.fetchall()
    return [dict(row) for row in rows]



def get_record_by_id(record_id):
    """根据 ID 获取单条记录。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (record_id,))
        row = cursor.fetchone()
    return dict(row) if row else None


def update_record(record_id, amount, category_l1, category_l2, date, note="", record_type="expense"):
    """修改一条已有记录的全部字段。

    参数：
        record_id: 要修改的记录 ID
        amount: 新金额（元）
        category_l1: 新一级分类
        category_l2: 新二级分类
        date: 新日期，格式 "2026-07-25"
        note: 新备注（可选）
        record_type: "expense"=支出 或 "income"=收入

    注意：会自动更新 updated_at 为当前时间。
    """
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE expenses
            SET amount = ?, type = ?, category_l1 = ?, category_l2 = ?, note = ?, date = ?, updated_at = ?
            WHERE id = ?
        ''', (amount, record_type, category_l1, category_l2, note, date, now, record_id))
        conn.commit()




def delete_record(record_id):
    """根据 ID 删除一条记录。

    参数：
        record_id: 要删除的记录 ID

    注意：删除后不可恢复，调用前应先弹出确认框让用户确认。
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (record_id,))
        conn.commit()




def get_records_by_date_range(start_date, end_date, record_type=None):
    """按日期范围查询记录，可按类型筛选。

    参数：
        start_date: 开始日期（包含），如 "2026-07-01"
        end_date: 结束日期（包含），如 "2026-07-31"
        record_type: 可选，"expense"=只看支出，"income"=只看收入，不填=看全部

    返回：
        记录列表，每条记录是一个字典，按日期倒序排列
    """
    with get_db() as conn:
        cursor = conn.cursor()
        if record_type:
            # 按日期范围 + 类型筛选（如只看本月支出）
            cursor.execute(
                'SELECT * FROM expenses WHERE date >= ? AND date <= ? AND type = ? ORDER BY date DESC',
                (start_date, end_date, record_type)
            )
        else:
            # 只按日期范围筛选，不区分支出/收入
            cursor.execute(
                'SELECT * FROM expenses WHERE date >= ? AND date <= ? ORDER BY date DESC',
                (start_date, end_date)
            )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]




def get_records_by_category(category_l1, category_l2=None, record_type=None):
    """按分类查询记录，可按二级分类和类型进一步筛选。

    参数：
        category_l1: 一级分类（必填），如"餐饮"
        category_l2: 二级分类（可选），如"午餐"，不填=查该一级分类下全部
        record_type: 可选，"expense"=只看支出，"income"=只看收入

    返回：
        记录列表，每条记录是一个字典，按日期倒序排列

    安全说明：WHERE 子句用 " AND ".join(conditions) 动态拼接，
    但 conditions 列表中的字符串都是写死的（如 "category_l1 = ?"），
    用户输入通过 params 列表用 ? 占位符安全传入。
    不要将用户输入直接加到 conditions 列表中。
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # 用列表动态拼接 SQL WHERE 条件，比写死多个 if/elif 分支更灵活
        # 注意：conditions 中的字符串都是硬编码的，用户值通过 params 的 ? 传入
        conditions = ["category_l1 = ?"]
        params = [category_l1]

        if category_l2:
            conditions.append("category_l2 = ?")
            params.append(category_l2)
        if record_type:
            conditions.append("type = ?")
            params.append(record_type)

        # 用 " AND " 把所有条件拼起来，变成类似 "category_l1 = ? AND category_l2 = ?"
        where = " AND ".join(conditions)
        # where 由固定的 condition 模板拼接而成，params 通过 ? 安全绑定，不存在注入风险
        cursor.execute(f'SELECT * FROM expenses WHERE {where} ORDER BY date DESC', params)
        rows = cursor.fetchall()
    return [dict(row) for row in rows]




def get_monthly_stats(year, month):
    """获取某月的完整统计报表。

    参数：
        year: 年份，如 2026
        month: 月份，如 7（1~12）

    返回：
        字典，包含：
        - total_expense: 本月总支出
        - total_income: 本月总收入
        - balance: 结余（收入 - 支出）
        - days: 有记录的天数
        - daily_avg: 日均支出
        - expense_by_category: 各支出分类的金额明细
        - income_by_category: 各收入分类的金额明细
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # 计算查询的起止日期，注意左闭右开：[start, end)
        # 比如查 7 月，就是 2026-07-01 到 2026-08-01（不包含后者）
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1}-01-01"  # 12 月的结束日期是次年 1 月 1 日
        else:
            end = f"{year}-{month + 1:02d}-01"

        # 查询一：本月总支出
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date < ? AND type = 'expense'",
            (start, end)
        )
        total_expense = cursor.fetchone()["total"]

        # 查询二：本月总收入
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date < ? AND type = 'income'",
            (start, end)
        )
        total_income = cursor.fetchone()["total"]

        # 查询三：按支出一级分类统计（比如餐饮花了多少、交通花了多少）
        cursor.execute(
            "SELECT category_l1, SUM(amount) as subtotal FROM expenses WHERE date >= ? AND date < ? AND type = 'expense' GROUP BY category_l1 ORDER BY subtotal DESC",
            (start, end)
        )
        expense_by_category = [{"category": row["category_l1"], "amount": row["subtotal"]} for row in cursor.fetchall()]

        # 查询四：按收入一级分类统计
        cursor.execute(
            "SELECT category_l1, SUM(amount) as subtotal FROM expenses WHERE date >= ? AND date < ? AND type = 'income' GROUP BY category_l1 ORDER BY subtotal DESC",
            (start, end)
        )
        income_by_category = [{"category": row["category_l1"], "amount": row["subtotal"]} for row in cursor.fetchall()]

        # 查询五：本月有记录的天数（用于计算日均支出）
        cursor.execute(
            'SELECT COUNT(DISTINCT date) as days FROM expenses WHERE date >= ? AND date < ?',
            (start, end)
        )
        days = cursor.fetchone()["days"] or 1

    return {
        "total_expense": total_expense,
        "total_income": total_income,
        "balance": round(total_income - total_expense, 2),
        "days": days,
        "daily_avg": round(total_expense / days, 2) if days > 0 else 0,
        "expense_by_category": expense_by_category,
        "income_by_category": income_by_category,
    }
