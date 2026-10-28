import sqlite3
import math
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from config import DATABASE_PATH, MAX_AMOUNT, MAX_CATEGORY_LENGTH, MAX_DESCRIPTION_LENGTH, MAX_LIST_LIMIT, ALLOWED_TOOLS
from validators import (
    validate_amount,
    validate_category,
    validate_description,
    validate_expense_date,
    validate_expense_id,
    validate_year_month,
    validate_limit,
    ValidationError,
)
from database import get_connection, initialize_database


# =========================================================
# CONFIGURATION
# =========================================================

mcp = FastMCP("Smart Expense Tracker")


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

try:
    initialize_database()
except sqlite3.Error as error:
    raise RuntimeError(f"Database initialization failed: {error}") from error


# =========================================================
# EXPENSE FORMATTING
# =========================================================

def format_expense(row):
    """
    Format an expense for the existing Streamlit app.
    Keep compatible format.
    """
    return (
        f"ID {row['id']} | "
        f"₹{row['amount']:.2f} | "
        f"{row['category']} | "
        f"{row['description'] or ''} | "
        f"{row['expense_date']}"
    )


# =========================================================
# ADD EXPENSE
# =========================================================

@mcp.tool()
def add_expense(amount: float, category: str, description: str = "", expense_date: str = "") -> str:
    try:
        amount = validate_amount(amount)
        category = validate_category(category)
        description = validate_description(description)

        if isinstance(expense_date, str):
            expense_date_clean = expense_date.strip()
        else:
            expense_date_clean = expense_date

        if not expense_date_clean:
            expense_date_clean = date.today().isoformat()

        expense_date_clean = validate_expense_date(expense_date_clean)

        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses (amount, category, description, expense_date)
                VALUES (?, ?, ?, ?)
                """,
                (amount, category, description, expense_date_clean),
            )
            expense_id = cursor.lastrowid

        return f"Expense added successfully. ID: {expense_id}"
    except ValidationError as error:
        return f"Error: {error}"
    except ValueError as error:
        return f"Error: {error}"
    except sqlite3.Error:
        return "Error: Unable to save expense to the database."


# =========================================================
# LIST EXPENSES
# =========================================================

@mcp.tool()
def list_expenses(limit: int = 5) -> str:
    try:
        limit = validate_limit(limit)
        query = """
            SELECT id, amount, category, description, expense_date
            FROM expenses
            ORDER BY id DESC
        """
        with get_connection() as conn:
            if limit == 0:
                rows = conn.execute(query).fetchall()
            else:
                rows = conn.execute(query + " LIMIT ?", (limit,)).fetchall()

        if not rows:
            return "No expenses have been recorded yet."
        return "\n".join(format_expense(row) for row in rows)
    except ValidationError as error:
        return f"Error: {error}"
    except ValueError as error:
        return f"Error: {error}"
    except sqlite3.Error:
        return "Error: Unable to retrieve expenses from the database."


# =========================================================
# GET EXPENSE
# =========================================================

@mcp.tool()
def get_expense(expense_id: int) -> dict:
    try:
        expense_id = validate_expense_id(expense_id)
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, amount, category, description, expense_date
                FROM expenses
                WHERE id = ?
                """,
                (expense_id,),
            ).fetchone()
        if row is None:
            return {"error": f"Expense ID {expense_id} was not found."}
        return dict(row)
    except ValidationError as error:
        return {"error": str(error)}
    except ValueError as error:
        return {"error": str(error)}
    except sqlite3.Error:
        return {"error": "Unable to retrieve expense from the database."}


# =========================================================
# UPDATE EXPENSE
# =========================================================

@mcp.tool()
def update_expense(expense_id: int, amount: float, category: str, description: str, expense_date: str) -> str:
    try:
        expense_id = validate_expense_id(expense_id)
        amount = validate_amount(amount)
        category = validate_category(category)
        description = validate_description(description)
        expense_date = validate_expense_date(expense_date)

        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE expenses
                SET amount = ?, category = ?, description = ?, expense_date = ?
                WHERE id = ?
                """,
                (amount, category, description, expense_date, expense_id),
            )
            if cursor.rowcount == 0:
                return f"Error: Expense ID {expense_id} was not found."
        return f"Expense ID {expense_id} updated successfully."
    except ValidationError as error:
        return f"Error: {error}"
    except ValueError as error:
        return f"Error: {error}"
    except sqlite3.Error:
        return "Error: Unable to update expense in the database."


# =========================================================
# DELETE EXPENSE
# =========================================================

@mcp.tool()
def delete_expense(expense_id: int) -> str:
    try:
        expense_id = validate_expense_id(expense_id)
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            if cursor.rowcount == 0:
                return f"Error: Expense ID {expense_id} was not found."
        return f"Expense ID {expense_id} deleted successfully."
    except ValidationError as error:
        return f"Error: {error}"
    except ValueError as error:
        return f"Error: {error}"
    except sqlite3.Error:
        return "Error: Unable to delete expense from the database."


# =========================================================
# MONTHLY TOTAL
# =========================================================

@mcp.tool()
def monthly_total(year: int, month: int) -> str:
    try:
        month_prefix = validate_year_month(year, month)
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE substr(expense_date, 1, 7) = ?",
                (month_prefix,),
            ).fetchone()
        total = round(float(row["total"]), 2)
        return f"Total expenses for {month_prefix}: ₹{total:.2f}"
    except ValidationError as error:
        return f"Error: {error}"
    except ValueError as error:
        return f"Error: {error}"
    except sqlite3.Error:
        return "Error: Unable to calculate monthly expenses."


# =========================================================
# TOP CATEGORIES
# =========================================================

@mcp.tool()
def top_categories(year: int, month: int) -> str:
    try:
        month_prefix = validate_year_month(year, month)
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT category, SUM(amount) AS total
                FROM expenses
                WHERE substr(expense_date, 1, 7) = ?
                GROUP BY category
                ORDER BY total DESC
                """,
                (month_prefix,),
            ).fetchall()
        if not rows:
            return "No expenses found for this month."
        results = []
        for row in rows:
            total = round(float(row["total"]), 2)
            results.append(f"{row['category']}: ₹{total:.2f}")
        return "\n".join(results)
    except ValidationError as error:
        return f"Error: {error}"
    except ValueError as error:
        return f"Error: {error}"
    except sqlite3.Error:
        return "Error: Unable to retrieve monthly category totals."


if __name__ == "__main__":
    mcp.run()
