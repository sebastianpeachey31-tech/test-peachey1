"""
单元测试 — 强哥帮你记 数据库模块
====================================
测试 db/database.py 中的所有函数。
使用临时数据库文件，不会影响你的真实记账数据。

运行方式：
    cd qiangge_bangniji
    python -m unittest discover tests/ -v
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import patch
import sqlite3

# 把项目根目录加到 Python 搜索路径，这样才能 import db.database
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================
# 第一组：纯函数测试（不需要数据库）
# ============================================================

class TestPureFunctions(unittest.TestCase):
    """测试 format_display 和 parse_display，这两个函数不涉及数据库。"""

    def test_format_display_known_category(self):
        """已知分类应该返回带 emoji 的名称，比如 '餐饮' -> '🍽️ 餐饮'"""
        from db.database import format_display
        self.assertEqual(format_display('餐饮'), '🍽️ 餐饮')
        self.assertEqual(format_display('交通'), '🚗 交通')
        self.assertEqual(format_display('购物'), '🛒 购物')

    def test_format_display_unknown_category(self):
        """不认识的分类用 📌 作为默认图标"""
        from db.database import format_display
        self.assertEqual(format_display('宇宙飞船'), '📌 宇宙飞船')

    def test_format_display_empty_string(self):
        """空字符串也应该能处理"""
        from db.database import format_display
        result = format_display('')
        self.assertTrue(result.startswith('📌'))

    def test_parse_display_normal(self):
        """正常去掉 emoji，比如 '🍽️ 餐饮' -> '餐饮'"""
        from db.database import parse_display
        self.assertEqual(parse_display('🍽️ 餐饮'), '餐饮')
        self.assertEqual(parse_display('🚗 交通'), '交通')

    def test_parse_display_no_emoji(self):
        """没有 emoji 前缀的文字原样返回"""
        from db.database import parse_display
        self.assertEqual(parse_display('餐饮'), '餐饮')
        self.assertEqual(parse_display('普通文字'), '普通文字')

    def test_parse_display_empty_string(self):
        """空字符串返回空字符串"""
        from db.database import parse_display
        self.assertEqual(parse_display(''), '')

    def test_format_then_parse_roundtrip(self):
        """format_display 之后再 parse_display，应该回到原始分类名"""
        from db.database import format_display, parse_display
        for name in ['餐饮', '交通', '购物', '月薪', '奖金', '日用品']:
            with self.subTest(name=name):
                self.assertEqual(parse_display(format_display(name)), name)


# ============================================================
# 第二组：数据库函数测试（用临时文件隔离，不影响真实数据）
# ============================================================

class TestDatabaseFunctions(unittest.TestCase):
    """测试所有需要数据库的函数。

    核心技巧：在 setUpClass 中把 DB_PATH 替换成临时文件路径，
    这样所有数据库操作都落在临时文件上，不会碰到用户的真实数据。
    """

    # ---- 类级别：创建临时数据库，替换真实路径 ----

    @classmethod
    def setUpClass(cls):
        """创建临时数据库文件，并替换 DB_PATH 指向它。"""
        # 创建一个临时文件作为测试数据库
        cls._tmpfile = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls._tmpfile.close()
        cls._tmp_path = cls._tmpfile.name

        # 用 mock 替换 DB_PATH，让所有函数读写临时文件
        cls._db_patcher = patch('db.database.DB_PATH', cls._tmp_path)
        cls._db_patcher.start()

        # 导入模块并初始化数据库结构
        import db.database as db
        cls.db = db
        cls.db.init_db()

    @classmethod
    def tearDownClass(cls):
        """清理：停止 mock，删除临时文件。"""
        cls._db_patcher.stop()
        try:
            os.unlink(cls._tmp_path)
        except OSError:
            pass

    # ---- 方法级别：每个测试前重置数据 ----

    def setUp(self):
        """每个测试前清空所有数据，保证测试之间互不影响。"""
        conn = sqlite3.connect(self._tmp_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses")
        cursor.execute("DELETE FROM categories")
        conn.commit()
        conn.close()
        # 重新填入预置分类
        self.db._seed_preset_categories()

    # ================================================================
    # 初始化测试
    # ================================================================

    def test_init_db_tables_exist(self):
        """init_db 应该创建 expenses 和 categories 两张表"""
        conn = sqlite3.connect(self._tmp_path)
        cursor = conn.cursor()
        # 查 sqlite_master 确认表存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('expenses', 'categories')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn('expenses', tables)
        self.assertIn('categories', tables)

    def test_init_db_seeds_preset_categories(self):
        """首次 init_db 应该写入预置分类（餐饮、交通等）"""
        cats = self.db.get_categories('expense')
        self.assertIn('餐饮', cats)
        self.assertIn('交通', cats)
        self.assertGreater(len(cats), 5)  # 至少有 5 个一级分类

    # ================================================================
    # add_record 测试
    # ================================================================

    def test_add_expense_record(self):
        """添加一条支出记录，应返回有效 ID，且数据正确"""
        rid = self.db.add_record(25.5, '餐饮', '午餐', '2026-07-24', '外卖', 'expense')
        self.assertIsNotNone(rid)
        self.assertGreater(rid, 0)

        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['amount'], 25.5)
        self.assertEqual(record['type'], 'expense')
        self.assertEqual(record['category_l1'], '餐饮')
        self.assertEqual(record['category_l2'], '午餐')
        self.assertEqual(record['date'], '2026-07-24')
        self.assertEqual(record['note'], '外卖')

    def test_add_income_record(self):
        """添加一条收入记录，type 应为 income"""
        rid = self.db.add_record(5000, '工资收入', '月薪', '2026-07-15', '', 'income')
        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['type'], 'income')
        self.assertEqual(record['amount'], 5000)
        self.assertEqual(record['category_l1'], '工资收入')

    def test_add_record_default_note(self):
        """不写备注时，note 应为空字符串"""
        rid = self.db.add_record(10, '交通', '公交地铁', '2026-07-24')
        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['note'], '')

    def test_add_record_default_type(self):
        """不指定 type 时，默认为 expense（支出）"""
        rid = self.db.add_record(10, '交通', '公交地铁', '2026-07-24')
        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['type'], 'expense')

    # ================================================================
    # get_all_records 测试
    # ================================================================

    def test_get_all_records_empty(self):
        """空数据库应返回空列表"""
        records = self.db.get_all_records()
        self.assertEqual(records, [])

    def test_get_all_records_with_data(self):
        """有数据时应返回所有记录"""
        self.db.add_record(10, '交通', '公交地铁', '2026-07-20')
        self.db.add_record(20, '餐饮', '午餐', '2026-07-21')
        records = self.db.get_all_records()
        self.assertEqual(len(records), 2)

    def test_get_all_records_order_date_desc(self):
        """默认按日期倒序（最新的在前）"""
        self.db.add_record(10, '交通', '公交地铁', '2026-07-20')
        self.db.add_record(20, '餐饮', '午餐', '2026-07-22')
        records = self.db.get_all_records('date DESC')
        self.assertEqual(records[0]['date'], '2026-07-22')

    def test_get_all_records_order_date_asc(self):
        """按日期正序（最早的在前）"""
        self.db.add_record(10, '交通', '公交地铁', '2026-07-20')
        self.db.add_record(20, '餐饮', '午餐', '2026-07-22')
        records = self.db.get_all_records('date ASC')
        self.assertEqual(records[0]['date'], '2026-07-20')

    def test_get_all_records_invalid_order_raises(self):
        """无效的排序参数应抛出 ValueError"""
        with self.assertRaises(ValueError):
            self.db.get_all_records('malicious; DROP TABLE expenses')

    # ================================================================
    # get_record_by_id 测试
    # ================================================================

    def test_get_record_by_id_exists(self):
        """存在的 ID 应返回记录字典"""
        rid = self.db.add_record(50, '购物', '日用品', '2026-07-24')
        record = self.db.get_record_by_id(rid)
        self.assertIsNotNone(record)
        self.assertIsInstance(record, dict)
        self.assertEqual(record['id'], rid)

    def test_get_record_by_id_not_exists(self):
        """不存在的 ID 应返回 None"""
        record = self.db.get_record_by_id(99999)
        self.assertIsNone(record)

    # ================================================================
    # update_record 测试
    # ================================================================

    def test_update_record_all_fields(self):
        """修改所有字段后应能正确读出"""
        rid = self.db.add_record(10, '餐饮', '午餐', '2026-07-20', '旧备注', 'expense')
        self.db.update_record(rid, 35, '交通', '公交地铁', '2026-07-21', '新备注', 'expense')
        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['amount'], 35)
        self.assertEqual(record['category_l1'], '交通')
        self.assertEqual(record['category_l2'], '公交地铁')
        self.assertEqual(record['date'], '2026-07-21')
        self.assertEqual(record['note'], '新备注')

    def test_update_record_change_type(self):
        """可以把支出改成收入"""
        rid = self.db.add_record(100, '其他', '日常杂项', '2026-07-20', '', 'expense')
        self.db.update_record(rid, 100, '其他收入', '退款报销', '2026-07-20', '', 'income')
        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['type'], 'income')
        self.assertEqual(record['category_l1'], '其他收入')

    # ================================================================
    # delete_record 测试
    # ================================================================

    def test_delete_record_exists(self):
        """删除存在的记录后应查不到"""
        rid = self.db.add_record(10, '餐饮', '午餐', '2026-07-24')
        self.db.delete_record(rid)
        record = self.db.get_record_by_id(rid)
        self.assertIsNone(record)

    def test_delete_record_not_exists(self):
        """删除不存在的记录不应报错（幂等操作）"""
        # 不应该抛出异常
        try:
            self.db.delete_record(99999)
        except Exception as e:
            self.fail(f'删除不存在的记录时抛出了异常: {e}')

    # ================================================================
    # get_records_by_date_range 测试
    # ================================================================

    def test_date_range_in_range(self):
        """记录日期在查询范围内应被查出"""
        self.db.add_record(10, '餐饮', '午餐', '2026-07-15')
        self.db.add_record(20, '交通', '公交地铁', '2026-07-20')
        records = self.db.get_records_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(records), 2)

    def test_date_range_out_of_range(self):
        """记录日期在查询范围外应查不到"""
        self.db.add_record(10, '餐饮', '午餐', '2026-06-01')
        records = self.db.get_records_by_date_range('2026-07-01', '2026-07-31')
        self.assertEqual(len(records), 0)

    def test_date_range_filter_by_type(self):
        """可以只查支出或只查收入"""
        self.db.add_record(10, '餐饮', '午餐', '2026-07-15', '', 'expense')
        self.db.add_record(5000, '工资收入', '月薪', '2026-07-15', '', 'income')
        expenses = self.db.get_records_by_date_range('2026-07-01', '2026-07-31', 'expense')
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0]['type'], 'expense')

    # ================================================================
    # get_records_by_category 测试
    # ================================================================

    def test_category_filter_l1_only(self):
        """只按一级分类筛选"""
        self.db.add_record(10, '餐饮', '午餐', '2026-07-24')
        self.db.add_record(15, '餐饮', '晚餐', '2026-07-24')
        self.db.add_record(5, '交通', '公交地铁', '2026-07-24')
        records = self.db.get_records_by_category('餐饮')
        self.assertEqual(len(records), 2)

    def test_category_filter_l1_and_l2(self):
        """按一级 + 二级分类筛选"""
        self.db.add_record(10, '餐饮', '午餐', '2026-07-24')
        self.db.add_record(15, '餐饮', '晚餐', '2026-07-24')
        records = self.db.get_records_by_category('餐饮', '午餐')
        self.assertEqual(len(records), 1)

    def test_category_filter_with_type(self):
        """分类 + 类型一起筛选"""
        self.db.add_record(10, '餐饮', '午餐', '2026-07-24', '', 'expense')
        self.db.add_record(5000, '工资收入', '月薪', '2026-07-24', '', 'income')
        records = self.db.get_records_by_category('餐饮', '午餐', 'expense')
        self.assertEqual(len(records), 1)

    def test_category_filter_empty_result(self):
        """查一个没有记录的分类应返回空列表"""
        records = self.db.get_records_by_category('不存在的分类')
        self.assertEqual(records, [])

    # ================================================================
    # get_monthly_stats 测试
    # ================================================================

    def test_monthly_stats_empty_month(self):
        """没有任何记录的月份，统计应为 0"""
        stats = self.db.get_monthly_stats(2026, 7)
        self.assertEqual(stats['total_expense'], 0)
        self.assertEqual(stats['total_income'], 0)
        self.assertEqual(stats['balance'], 0)

    def test_monthly_stats_with_data(self):
        """有记录的月份应正确统计"""
        self.db.add_record(30, '餐饮', '午餐', '2026-07-10', '', 'expense')
        self.db.add_record(20, '交通', '公交地铁', '2026-07-15', '', 'expense')
        self.db.add_record(5000, '工资收入', '月薪', '2026-07-01', '', 'income')

        stats = self.db.get_monthly_stats(2026, 7)
        self.assertEqual(stats['total_expense'], 50)
        self.assertEqual(stats['total_income'], 5000)
        self.assertEqual(stats['balance'], 4950)
        self.assertEqual(len(stats['expense_by_category']), 2)

    def test_monthly_stats_december_boundary(self):
        """12 月的日期边界应正确处理（跨年）"""
        self.db.add_record(100, '购物', '日用品', '2026-12-25', '', 'expense')
        stats = self.db.get_monthly_stats(2026, 12)
        self.assertEqual(stats['total_expense'], 100)

    # ================================================================
    # get_categories / get_all_category_l1 测试
    # ================================================================

    def test_get_categories_expense(self):
        """获取支出分类"""
        cats = self.db.get_categories('expense')
        self.assertIsInstance(cats, dict)
        self.assertIn('餐饮', cats)
        self.assertIsInstance(cats['餐饮'], list)
        self.assertIn('午餐', cats['餐饮'])

    def test_get_categories_income(self):
        """获取收入分类"""
        cats = self.db.get_categories('income')
        self.assertIsInstance(cats, dict)
        self.assertIn('工资收入', cats)
        self.assertIn('月薪', cats['工资收入'])

    def test_get_all_category_l1_expense(self):
        """获取支出一级分类列表"""
        l1_list = self.db.get_all_category_l1('expense')
        self.assertIn('餐饮', l1_list)
        self.assertIn('交通', l1_list)
        self.assertGreater(len(l1_list), 5)

    def test_get_all_category_l1_income(self):
        """获取收入一级分类列表"""
        l1_list = self.db.get_all_category_l1('income')
        self.assertIn('工资收入', l1_list)
        self.assertIn('投资收益', l1_list)

    # ================================================================
    # is_preset_category 测试
    # ================================================================

    def test_is_preset_true(self):
        """预置分类应返回 True"""
        self.assertTrue(self.db.is_preset_category('expense', '餐饮', '午餐'))

    def test_is_preset_false(self):
        """不存在的分类应返回 False"""
        self.assertFalse(self.db.is_preset_category('expense', '不存在的', '分类'))

    # ================================================================
    # add_category 测试（新增用户自定义分类）
    # ================================================================

    def test_add_category_success(self):
        """成功新增一个自定义分类"""
        ok, err = self.db.add_category('expense', '其他', '测试分类')
        self.assertTrue(ok)
        self.assertIsNone(err)
        # 确认可以查到
        self.assertTrue(self.db.is_preset_category('expense', '其他', '测试分类') is False)
        # 查一下确实存在
        cats = self.db.get_categories('expense')
        self.assertIn('测试分类', cats.get('其他', []))

    def test_add_category_empty_name(self):
        """空名称应拒绝"""
        ok, err = self.db.add_category('expense', '', '午餐')
        self.assertFalse(ok)
        self.assertIn('不能为空', err)

    def test_add_category_duplicate(self):
        """重复的分类应拒绝"""
        self.db.add_category('expense', '其他', '测试分类')
        ok, err = self.db.add_category('expense', '其他', '测试分类')
        self.assertFalse(ok)
        self.assertIn('已存在', err)

    # ================================================================
    # update_category_name 测试（改名分类）
    # ================================================================

    def test_update_category_name_success(self):
        """成功改名自定义分类"""
        self.db.add_category('expense', '其他', '旧分类名')
        ok, err = self.db.update_category_name('expense', '其他', '旧分类名', '其他', '新分类名')
        self.assertTrue(ok)
        cats = self.db.get_categories('expense')
        self.assertIn('新分类名', cats.get('其他', []))

    def test_update_category_name_preset_rejected(self):
        """预置分类不能改名"""
        ok, err = self.db.update_category_name('expense', '餐饮', '午餐', '餐饮', '豪华午餐')
        self.assertFalse(ok)
        self.assertIn('预置', err)

    def test_update_category_name_empty_rejected(self):
        """新名称为空应拒绝"""
        self.db.add_category('expense', '其他', '旧分类名')
        ok, err = self.db.update_category_name('expense', '其他', '旧分类名', '', '')
        self.assertFalse(ok)
        self.assertIn('不能为空', err)

    def test_update_category_name_not_found(self):
        """不存在的分类改名应失败"""
        ok, err = self.db.update_category_name('expense', '不存在', '不存在', '新L1', '新L2')
        self.assertFalse(ok)
        self.assertIn('不存在', err)

    def test_update_category_name_syncs_expenses(self):
        """改名分类后，已有记录的分类也应同步更新"""
        self.db.add_category('expense', '其他', '旧分类名')
        rid = self.db.add_record(50, '其他', '旧分类名', '2026-07-24', '', 'expense')
        self.db.update_category_name('expense', '其他', '旧分类名', '其他', '新分类名')
        record = self.db.get_record_by_id(rid)
        self.assertEqual(record['category_l1'], '其他')
        self.assertEqual(record['category_l2'], '新分类名')

    # ================================================================
    # delete_category 测试（删除分类）
    # ================================================================

    def test_delete_category_success(self):
        """成功删除一个没有记录在用的自定义分类"""
        self.db.add_category('expense', '其他', '待删除分类')
        ok, err = self.db.delete_category('expense', '其他', '待删除分类')
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_delete_category_preset_rejected(self):
        """预置分类不能删除"""
        ok, err = self.db.delete_category('expense', '餐饮', '午餐')
        self.assertFalse(ok)
        self.assertIn('预置', err)

    def test_delete_category_not_found(self):
        """删除不存在的分类应失败"""
        ok, err = self.db.delete_category('expense', '不存在', '不存在')
        self.assertFalse(ok)

    def test_delete_category_with_records_rejected(self):
        """有记录在用的分类不能删除"""
        self.db.add_category('expense', '其他', '有记录的分类')
        self.db.add_record(100, '其他', '有记录的分类', '2026-07-24', '', 'expense')
        ok, err = self.db.delete_category('expense', '其他', '有记录的分类')
        self.assertFalse(ok)
        self.assertIn('条记录', err)


# ============================================================
# 运行入口
# ============================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
