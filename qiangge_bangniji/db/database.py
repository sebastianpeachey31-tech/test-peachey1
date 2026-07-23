"""
数据库模块 - 管理 SQLite 数据库的创建、连接和操作。
"""
import sqlite3
import os
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


def init_db():
    """初始化数据库：创建表结构，如果有旧版表则自动升级。"""
    conn = get_connection()
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
    conn.close()

    # 首次启动时写入预置分类种子数据
    _seed_preset_categories()


def _seed_preset_categories():
    """首次运行时将硬编码的预置分类写入 categories 表。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM categories')
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
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
    conn.close()


# ============================================================
# 分类管理：查询、新增、改名、删除
# ============================================================

def get_categories(cat_type):
    """返回指定类型的分类字典 {一级分类: [二级分类列表]}，按 sort_order 排序。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT category_l1, category_l2 FROM categories '
        'WHERE type = ? ORDER BY sort_order',
        (cat_type,)
    )
    rows = cursor.fetchall()
    conn.close()

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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT is_preset FROM categories '
        'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
        (cat_type, category_l1, category_l2)
    )
    row = cursor.fetchone()
    conn.close()
    return bool(row['is_preset']) if row else False


def add_category(cat_type, category_l1, category_l2):
    """新增一个用户自定义分类（is_preset=0）。返回 (True, None) 或 (False, 错误原因)。"""
    # 不允许空名称
    if not category_l1.strip() or not category_l2.strip():
        return False, "分类名称不能为空"

    conn = get_connection()
    cursor = conn.cursor()

    # 检查是否重复
    cursor.execute(
        'SELECT COUNT(*) as cnt FROM categories '
        'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
        (cat_type, category_l1.strip(), category_l2.strip())
    )
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
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
    conn.close()
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

    conn = get_connection()
    cursor = conn.cursor()

    # 验证是用户自定义分类
    cursor.execute(
        'SELECT is_preset FROM categories '
        'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
        (cat_type, old_l1, old_l2)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "分类不存在"
    if row['is_preset']:
        conn.close()
        return False, "预置分类不可修改"

    # 检查新名称是否与已有分类重复
    if old_l1 != new_l1 or old_l2 != new_l2:
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM categories '
            'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
            (cat_type, new_l1, new_l2)
        )
        if cursor.fetchone()['cnt'] > 0:
            conn.close()
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
    conn.close()
    return True, None


def delete_category(cat_type, category_l1, category_l2):
    """
    删除用户自定义分类（is_preset=0）。
    如果有 expenses 记录在用则拒绝删除。
    返回 (True, None) 或 (False, 错误原因)。
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 验证是用户自定义分类
    cursor.execute(
        'SELECT is_preset FROM categories '
        'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
        (cat_type, category_l1, category_l2)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "分类不存在"
    if row['is_preset']:
        conn.close()
        return False, "预置分类不可删除"

    # 检查是否有记录在使用
    cursor.execute(
        'SELECT COUNT(*) as cnt FROM expenses '
        'WHERE type = ? AND category_l1 = ? AND category_l2 = ?',
        (cat_type, category_l1, category_l2)
    )
    count = cursor.fetchone()['cnt']
    if count > 0:
        conn.close()
        return False, f"该分类被 {count} 条记录使用，请先修改这些记录后再删除"

    cursor.execute(
        'DELETE FROM categories '
        'WHERE type = ? AND category_l1 = ? AND category_l2 = ? AND is_preset = 0',
        (cat_type, category_l1, category_l2)
    )
    conn.commit()
    conn.close()
    return True, None


# ============================================================
# CRUD 操作：增删改查
# ============================================================

def add_record(amount, category_l1, category_l2, date, note="", record_type="expense"):
    """添加一条记录（支出或收入）。"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO expenses (amount, type, category_l1, category_l2, note, date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (amount, record_type, category_l1, category_l2, note, date, now, now))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def get_all_records(order="date DESC"):
    """获取所有记录，默认按日期倒序。"""
    # 只允许安全的排序字段，防 SQL 注入
    ALLOWED_ORDERS = {"date ASC", "date DESC", "amount ASC", "amount DESC"}
    if order not in ALLOWED_ORDERS:
        raise ValueError(f"无效的排序参数: {order}")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM expenses ORDER BY {order}')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]



def get_record_by_id(record_id):
    """根据 ID 获取单条记录。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_record(record_id, amount, category_l1, category_l2, date, note="", record_type="expense"):
    """修改一条记录。"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE expenses
        SET amount = ?, type = ?, category_l1 = ?, category_l2 = ?, note = ?, date = ?, updated_at = ?
        WHERE id = ?
    ''', (amount, record_type, category_l1, category_l2, note, date, now, record_id))
    conn.commit()
    conn.close()




def delete_record(record_id):
    """删除一条记录。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()




def get_records_by_date_range(start_date, end_date, record_type=None):
    """按日期范围查询记录，可按类型筛选。"""
    conn = get_connection()
    cursor = conn.cursor()
    if record_type:
        cursor.execute(
            'SELECT * FROM expenses WHERE date >= ? AND date <= ? AND type = ? ORDER BY date DESC',
            (start_date, end_date, record_type)
        )
    else:
        cursor.execute(
            'SELECT * FROM expenses WHERE date >= ? AND date <= ? ORDER BY date DESC',
            (start_date, end_date)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]




def get_records_by_category(category_l1, category_l2=None, record_type=None):
    """按分类查询记录，可按类型筛选。"""
    conn = get_connection()
    cursor = conn.cursor()

    conditions = ["category_l1 = ?"]
    params = [category_l1]

    if category_l2:
        conditions.append("category_l2 = ?")
        params.append(category_l2)
    if record_type:
        conditions.append("type = ?")
        params.append(record_type)

    where = " AND ".join(conditions)
    cursor.execute(f'SELECT * FROM expenses WHERE {where} ORDER BY date DESC', params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]




def get_monthly_stats(year, month):
    """获取某月统计：总支出、总收入、结余、各分类合计。"""
    conn = get_connection()
    cursor = conn.cursor()
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    # 总支出
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date < ? AND type = 'expense'",
        (start, end)
    )
    total_expense = cursor.fetchone()["total"]

    # 总收入
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date < ? AND type = 'income'",
        (start, end)
    )
    total_income = cursor.fetchone()["total"]

    # 按支出分类统计
    cursor.execute(
        "SELECT category_l1, SUM(amount) as subtotal FROM expenses WHERE date >= ? AND date < ? AND type = 'expense' GROUP BY category_l1 ORDER BY subtotal DESC",
        (start, end)
    )
    expense_by_category = [{"category": row["category_l1"], "amount": row["subtotal"]} for row in cursor.fetchall()]

    # 按收入分类统计
    cursor.execute(
        "SELECT category_l1, SUM(amount) as subtotal FROM expenses WHERE date >= ? AND date < ? AND type = 'income' GROUP BY category_l1 ORDER BY subtotal DESC",
        (start, end)
    )
    income_by_category = [{"category": row["category_l1"], "amount": row["subtotal"]} for row in cursor.fetchall()]

    # 记录天数
    cursor.execute(
        'SELECT COUNT(DISTINCT date) as days FROM expenses WHERE date >= ? AND date < ?',
        (start, end)
    )
    days = cursor.fetchone()["days"] or 1

    conn.close()
    return {
        "total_expense": total_expense,
        "total_income": total_income,
        "balance": round(total_income - total_expense, 2),
        "days": days,
        "daily_avg": round(total_expense / days, 2) if days > 0 else 0,
        "expense_by_category": expense_by_category,
        "income_by_category": income_by_category,
    }
