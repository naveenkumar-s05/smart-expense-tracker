import sqlite3
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Smart Expense Tracker")

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "expenses.db"


def get_connection():
    """Open a connection to the local SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create the expenses table if it does not exist."""
    with get_connection() as conn:
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


def format_expense(row):
    return (
        f"ID {row['id']} | ₹{row['amount']:.2f} | "
        f"{row['category']} | {row['description'] or ''} | "
        f"{row['expense_date']}"
    )


initialize_database()


@mcp.tool()
def add_expense(amount: float, category: str, description: str = "",
                expense_date: str = "") -> str:
    """Record an expense."""
    if amount <= 0:
        return "Error: Amount must be greater than zero."
    category = category.strip().title()
    if not category:
        return "Error: Category cannot be empty."
    expense_date = expense_date.strip() or date.today().isoformat()
    try:
        date.fromisoformat(expense_date)
    except ValueError:
        return "Error: Date must use YYYY-MM-DD format."

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO expenses (amount, category, description, expense_date)
               VALUES (?, ?, ?, ?)""",
            (amount, category, description.strip(), expense_date),
        )
        expense_id = cursor.lastrowid
    return f"Expense added successfully. ID: {expense_id}"


@mcp.tool()
def list_expenses(limit: int = 5) -> str:
    """List latest five expenses by default. Use limit=0 to list all."""
    if limit < 0:
        return "Error: Limit cannot be negative."
    with get_connection() as conn:
        query = """SELECT id, amount, category, description, expense_date
                   FROM expenses ORDER BY id DESC"""
        rows = conn.execute(query if limit == 0 else query + " LIMIT ?",
                            () if limit == 0 else (limit,)).fetchall()
    if not rows:
        return "No expenses have been recorded yet."
    return "\n".join(format_expense(row) for row in rows)


@mcp.tool()
def get_expense(expense_id: int) -> dict:
    """Get one expense by ID, for editing."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id, amount, category, description, expense_date
               FROM expenses WHERE id = ?""", (expense_id,)
        ).fetchone()
    if row is None:
        return {"error": f"Expense ID {expense_id} was not found."}
    return dict(row)


@mcp.tool()
def update_expense(expense_id: int, amount: float, category: str,
                   description: str, expense_date: str) -> str:
    """Update an existing expense."""
    if amount <= 0:
        return "Error: Amount must be greater than zero."
    category = category.strip().title()
    if not category:
        return "Error: Category cannot be empty."
    try:
        date.fromisoformat(expense_date)
    except ValueError:
        return "Error: Date must use YYYY-MM-DD format."

    with get_connection() as conn:
        cursor = conn.execute(
            """UPDATE expenses
               SET amount = ?, category = ?, description = ?, expense_date = ?
               WHERE id = ?""",
            (amount, category, description.strip(), expense_date, expense_id),
        )
    if cursor.rowcount == 0:
        return f"Error: Expense ID {expense_id} was not found."
    return f"Expense ID {expense_id} updated successfully."


@mcp.tool()
def delete_expense(expense_id: int) -> str:
    """Delete an expense by ID."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    if cursor.rowcount == 0:
        return f"Error: Expense ID {expense_id} was not found."
    return f"Expense ID {expense_id} deleted successfully."


@mcp.tool()
def monthly_total(year: int, month: int) -> str:
    """Calculate total spending for a selected month."""
    if not 1 <= month <= 12:
        return "Error: Month must be from 1 to 12."
    month_prefix = f"{year:04d}-{month:02d}"
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) AS total FROM expenses
               WHERE substr(expense_date, 1, 7) = ?""", (month_prefix,)
        ).fetchone()
    return f"Total expenses for {month_prefix}: ₹{row['total']:.2f}"


@mcp.tool()
def top_categories(year: int, month: int) -> str:
    """Return totals grouped by category for a month."""
    if not 1 <= month <= 12:
        return "Error: Month must be from 1 to 12."
    month_prefix = f"{year:04d}-{month:02d}"
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT category, SUM(amount) AS total FROM expenses
               WHERE substr(expense_date, 1, 7) = ?
               GROUP BY category ORDER BY total DESC""", (month_prefix,)
        ).fetchall()
    if not rows:
        return "No expenses found for this month."
    return "\n".join(f"{row['category']}: ₹{row['total']:.2f}" for row in rows)


if __name__ == "__main__":
    mcp.run()
