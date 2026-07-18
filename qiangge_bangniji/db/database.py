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

# 默认分类（用于向后兼容的引用）
CATEGORIES = EXPENSE_CATEGORIES


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

    conn.commit()
    conn.close()


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


# 兼容旧接口
add_expense = add_record


def get_all_records(order="date DESC"):
    """获取所有记录，默认按日期倒序。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM expenses ORDER BY {order}')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


get_all_expenses = get_all_records


def get_record_by_id(record_id):
    """根据 ID 获取单条记录。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


get_expense_by_id = get_record_by_id


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


update_expense = update_record


def delete_record(record_id):
    """删除一条记录。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()


delete_expense = delete_record


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


get_expenses_by_date_range = get_records_by_date_range


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


get_expenses_by_category = get_records_by_category


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
