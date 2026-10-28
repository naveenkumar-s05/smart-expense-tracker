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


class TestValidation(unittest.TestCase):
    def test_invalid_date_format(self):
        res = server.add_expense(10, "Food", "x", "17-10-2026")
        self.assertIn("Error", res)

    def test_future_date_ok(self):  # policy not explicitly forbidding future, just validate format
        res = server.add_expense(10, "Food", "x", "2099-12-31")
        # Should be valid format
        self.assertNotIn("Error: Date must", res)


if __name__ == '__main__':
    unittest.main()
