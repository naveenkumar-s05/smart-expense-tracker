import os
import tempfile
import unittest
import sqlite3
from pathlib import Path

# Set up test db
test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
os.close(test_db_fd)

# Override before importing modules
import config
config.DATABASE_PATH = Path(test_db_path)
import database
database.DATABASE_PATH = Path(test_db_path)
database.initialize_database()

import server


class TestCRUD(unittest.TestCase):
    def setUp(self):
        # Clear table
        with database.get_connection() as conn:
            conn.execute("DELETE FROM expenses")

    def test_add_expense_valid(self):
        res = server.add_expense(100, "Food", "Lunch", "2026-10-17")
        self.assertIn("Expense added successfully", res)

    def test_add_expense_zero_amount(self):
        res = server.add_expense(0, "Food", "Lunch", "2026-10-17")
        self.assertIn("Error", res)

    def test_add_expense_negative_amount(self):
        res = server.add_expense(-10, "Food", "Lunch", "2026-10-17")
        self.assertIn("Error", res)

    def test_add_expense_bool_amount(self):
        res = server.add_expense(True, "Food", "Lunch", "2026-10-17")
        self.assertIn("Error", res)

    def test_add_expense_empty_category(self):
        res = server.add_expense(10, "   ", "Lunch", "2026-10-17")
        self.assertIn("Error", res)

    def test_list_expenses_empty(self):
        res = server.list_expenses(5)
        self.assertIn("No expenses", res)

    def test_get_expense_invalid_id(self):
        res = server.get_expense(0)
        self.assertIn("error", res)

    def test_get_expense_not_found(self):
        res = server.get_expense(9999)
        self.assertIn("error", res)

    def test_update_expense_not_found(self):
        res = server.update_expense(9999, 10, "Food", "x", "2026-10-17")
        self.assertIn("Error", res)

    def test_delete_expense_not_found(self):
        res = server.delete_expense(9999)
        self.assertIn("Error", res)

    def test_monthly_total_empty(self):
        res = server.monthly_total(2026, 10)
        self.assertIn("0.00", res)


if __name__ == '__main__':
    unittest.main()
