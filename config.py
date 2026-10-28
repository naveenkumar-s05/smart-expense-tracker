import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "expenses.db"
CONFIG_DB_PATH = BASE_DIR / "config.db"

MAX_AMOUNT = 999999.99
MAX_CATEGORY_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 500
MAX_LIST_LIMIT = 10000

ALLOWED_TOOLS = {
    "add_expense",
    "list_expenses",
    "get_expense",
    "update_expense",
    "delete_expense",
    "monthly_total",
    "top_categories",
}
