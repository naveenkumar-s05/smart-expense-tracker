import os
import tempfile
import unittest
from pathlib import Path

test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
os.close(test_db_fd)

import config
config.DATABASE_PATH = Path(test_db_path)
import database
database.DATABASE_PATH = Path(test_db_path)
database.initialize_database()

import server


class TestFinancial(unittest.TestCase):
    def setUp(self):
        with database.get_connection() as conn:
            conn.execute("DELETE FROM expenses")

    def test_monthly_total_multiple(self):
        server.add_expense(100, "Food", "a", "2026-01-05")
        server.add_expense(50, "Food", "b", "2026-01-15")
        res = server.monthly_total(2026, 1)
        self.assertIn("150.00", res)

    def test_category_totals(self):
        server.add_expense(100, "Food", "a", "2026-02-01")
        server.add_expense(200, "Transport", "b", "2026-02-01")
        res = server.top_categories(2026, 2)
        self.assertIn("Food", res)
        self.assertIn("Transport", res)


if __name__ == '__main__':
    unittest.main()
