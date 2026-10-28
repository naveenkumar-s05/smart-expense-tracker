import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config import DATABASE_PATH, CONFIG_DB_PATH


@contextmanager
def get_connection(db_path=None):
    if db_path is None:
        db_path = DATABASE_PATH
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    with get_connection(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                description TEXT DEFAULT '',
                expense_date TEXT NOT NULL
            )
            """
        )
        # Add indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)")


def initialize_config_db():
    with get_connection(CONFIG_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                monthly_budget REAL NOT NULL CHECK(monthly_budget > 0),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )


# Budget functions
def get_monthly_budget(default=6000.0):
    initialize_config_db()
    try:
        with get_connection(CONFIG_DB_PATH) as conn:
            row = conn.execute("SELECT monthly_budget FROM budget_config WHERE id = 1").fetchone()
            if row:
                return float(row["monthly_budget"])
            return float(default)
    except Exception:
        return float(default)


def set_monthly_budget(budget):
    from validators import validate_amount
    budget_validated = validate_amount(budget)
    if budget_validated <= 0:
        raise ValueError("Budget must be greater than zero.")
    initialize_config_db()
    with get_connection(CONFIG_DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO budget_config (id, monthly_budget, updated_at)
            VALUES (1, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                monthly_budget = excluded.monthly_budget,
                updated_at = datetime('now')
            """,
            (budget_validated,),
        )
    return budget_validated
