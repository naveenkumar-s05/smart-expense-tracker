import asyncio
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI


# ==========================================================
# CONFIGURATION
# ==========================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = BASE_DIR / "server.py"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

if not OPENROUTER_API_KEY:
    st.error("OPENROUTER_API_KEY is missing from your .env file.")
    st.stop()

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


# ==========================================================
# MCP CONNECTION
# ==========================================================

def get_server_parameters():
    return StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=os.environ.copy(),
    )


async def call_mcp_tool_async(tool_name, arguments=None):
    """Connect to the local MCP server and call one tool."""
    arguments = arguments or {}

    async with stdio_client(get_server_parameters()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            if result.structuredContent is not None:
                return result.structuredContent

            text_parts = [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ]

            return "\n".join(text_parts)


def call_mcp_tool(tool_name, arguments=None):
    return asyncio.run(call_mcp_tool_async(tool_name, arguments))


def unwrap_result(result):
    """Remove a common MCP result wrapper, if present."""
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    return result


# ==========================================================
# EXPENSE DISPLAY HELPERS
# ==========================================================

def parse_expense_list(result):
    result = unwrap_result(result)

    if not isinstance(result, str):
        result = str(result)

    expenses = []

    if "No expenses have been recorded" in result:
        return expenses

    for line in result.splitlines():
        line = line.strip()

        if not line.startswith("ID "):
            continue

        try:
            parts = [part.strip() for part in line.split("|")]

            expenses.append({
                "id": int(parts[0].replace("ID", "").strip()),
                "amount": float(parts[1].replace("₹", "").strip()),
                "category": parts[2],
                "description": parts[3] if len(parts) > 3 else "",
                "date": parts[4] if len(parts) > 4 else "",
            })

        except (ValueError, IndexError):
            continue

    return expenses


def load_expenses(limit=5):
    result = call_mcp_tool("list_expenses", {"limit": limit})
    return parse_expense_list(result)


def load_one_expense(expense_id):
    result = call_mcp_tool(
        "get_expense",
        {"expense_id": int(expense_id)},
    )

    result = unwrap_result(result)

    if isinstance(result, dict):
        return result

    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return None

    return None


def parse_rupee_amount(result):
    result = unwrap_result(result)
    match = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", str(result))

    if not match:
        return 0.0

    return float(match.group(1).replace(",", ""))


def parse_category_totals(result):
    result = unwrap_result(result)
    rows = []

    for line in str(result).splitlines():
        match = re.match(
            r"^\s*(.+?)\s*:\s*₹\s*([\d,]+(?:\.\d+)?)\s*$",
            line,
        )

        if match:
            rows.append({
                "Category": match.group(1).strip(),
                "Amount (₹)": float(match.group(2).replace(",", "")),
            })

    return rows


# ==========================================================
# MCP TOOLS EXPOSED TO THE AI CHAT
# ==========================================================

AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Add a new expense to the user's expense tracker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Expense amount in rupees.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Expense category, such as Food, Travel, Shopping, Bills.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Short description of the expense.",
                    },
                    "expense_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    },
                },
                "required": ["amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_expenses",
            "description": "List recent expenses. Use limit=0 to list all expenses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of expenses. Default 5; use 0 for all.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense",
            "description": "Get the details of one expense by its database ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "integer"},
                },
                "required": ["expense_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_expense",
            "description": "Update an existing expense by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "integer"},
                    "amount": {"type": "number"},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "expense_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    },
                },
                "required": [
                    "expense_id",
                    "amount",
                    "category",
                    "description",
                    "expense_date",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_expense",
            "description": "Delete an expense by database ID. Confirm the target expense with the user before deleting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "integer"},
                },
                "required": ["expense_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "monthly_total",
            "description": "Calculate total spending for a selected year and month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_categories",
            "description": "Get monthly spending totals grouped by category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                },
                "required": ["year", "month"],
            },
        },
    },
]


# ==========================================================
# AI CHAT + TOOL EXECUTION
# ==========================================================

SYSTEM_PROMPT = """
You are the helpful AI assistant inside a Smart Expense Tracker.

You can use the provided expense tools to read and manage the user's expenses.

Rules:
- Use tools when the user asks about saved expenses or monthly totals.
- Do not claim an expense was added, updated, or deleted unless the tool confirms it.
- When adding an expense and the date is not specified, use today's date.
- Today's date is provided in the user message.
- Before deleting an expense, ask the user to confirm which expense should be deleted.
- If the user has not provided enough information to add or update an expense, ask a brief clarification.
- Display money in Indian rupees (₹).
- Do not invent expense records or totals.
"""


def run_ai_chat(user_text):
    """Send a user message to OpenRouter and execute requested MCP tools."""
    today = date.today().isoformat()

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_text,
    })

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\nToday's date: {today}",
        }
    ]

    # Send conversation history, but not UI-only metadata.
    for message in st.session_state.chat_messages:
        messages.append({
            "role": message["role"],
            "content": message.get("content", ""),
        })

    # Allow the model several rounds of tool calls.
    for _ in range(5):
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=AI_TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        if not assistant_message.tool_calls:
            answer = assistant_message.content or "I couldn't generate a response."

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": answer,
            })

            return answer

        # Append assistant tool-call message in OpenAI-compatible format.
        messages.append(assistant_message.model_dump(exclude_none=True))

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            # Require explicit confirmation before executing a delete.
            if tool_name == "delete_expense":
                expense_id = arguments.get("expense_id")

                st.session_state["pending_chat_delete_id"] = expense_id

                tool_result = (
                    f"Deletion of expense ID {expense_id} has NOT been performed. "
                    "Ask the user to confirm deletion using the app's confirmation button."
                )

            else:
                try:
                    tool_result = call_mcp_tool(tool_name, arguments)
                    tool_result = unwrap_result(tool_result)

                except Exception as error:
                    tool_result = f"Tool error: {error}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": (
                    json.dumps(tool_result, ensure_ascii=False)
                    if not isinstance(tool_result, str)
                    else tool_result
                ),
            })

    answer = "I reached the tool-call limit for this message. Please try a simpler request."

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": answer,
    })

    return answer


# ==========================================================
# STREAMLIT PAGE
# ==========================================================

st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Smart Expense Tracker")
st.caption("Manage expenses and ask your AI assistant about your spending.")


# ==========================================================
# ADD EXPENSE FORM
# ==========================================================

st.header("➕ Add an expense")

with st.form("add_expense_form", clear_on_submit=True):
    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0,
        value=0.00,
        step=1.00,
        format="%.2f",
    )

    category = st.selectbox(
        "Category",
        [
            "Food",
            "Transport",
            "Shopping",
            "Bills",
            "Health",
            "Education",
            "Entertainment",
            "Other",
        ],
    )

    description = st.text_input("Description", placeholder="e.g. Lunch")
    expense_date = st.date_input("Expense date")

    submitted = st.form_submit_button("Save expense")

    if submitted:
        try:
            result = call_mcp_tool(
                "add_expense",
                {
                    "amount": float(amount),
                    "category": category,
                    "description": description,
                    "expense_date": expense_date.isoformat(),
                },
            )

            st.success(str(unwrap_result(result)))
            st.rerun()

        except Exception as error:
            st.error(f"Could not save expense: {error}")


st.divider()


# ==========================================================
# RECENT EXPENSES TABLE WITH SAME-ROW ACTIONS
# ==========================================================

st.header("🧾 Recent expenses")

try:
    recent_expenses = load_expenses(limit=5)
except Exception as error:
    st.error(f"Could not load recent expenses: {error}")
    recent_expenses = []

if not recent_expenses:
    st.info("No expenses have been recorded yet.")
else:
    widths = [0.55, 0.55, 1.0, 1.0, 1.8, 1.2, 0.55, 0.65]
    headers = [
        "S.No.", "ID", "Amount (₹)", "Category",
        "Description", "Date", "Edit", "Delete",
    ]

    header_cols = st.columns(widths)

    for col, heading in zip(header_cols, headers):
        col.markdown(f"**{heading}**")

    st.divider()

    for serial, expense in enumerate(recent_expenses, start=1):
        cols = st.columns(widths)

        cols[0].write(serial)
        cols[1].write(expense["id"])
        cols[2].write(f'{expense["amount"]:,.2f}')
        cols[3].write(expense["category"])
        cols[4].write(expense["description"] or "—")
        cols[5].write(expense["date"])

        if cols[6].button("✏️", key=f'edit_{expense["id"]}'):
            st.session_state["editing_expense_id"] = expense["id"]
            st.rerun()

        if cols[7].button("🗑️", key=f'delete_{expense["id"]}'):
            st.session_state["confirm_delete_id"] = expense["id"]
            st.rerun()

        st.divider()


# ==========================================================
# VIEW ALL EXPENSES
# ==========================================================

if st.button("View all expenses"):
    st.session_state["show_all_expenses"] = True

if st.session_state.get("show_all_expenses"):
    try:
        all_expenses = load_expenses(limit=0)

        all_rows = [
            {
                "S.No.": serial,
                "ID": expense["id"],
                "Amount (₹)": f'{expense["amount"]:,.2f}',
                "Category": expense["category"],
                "Description": expense["description"],
                "Date": expense["date"],
            }
            for serial, expense in enumerate(all_expenses, start=1)
        ]

        st.dataframe(
            all_rows,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"Could not load all expenses: {error}")

    if st.button("Hide full list"):
        st.session_state["show_all_expenses"] = False
        st.rerun()


# ==========================================================
# EDIT EXPENSE FORM
# ==========================================================

editing_id = st.session_state.get("editing_expense_id")

if editing_id is not None:
    st.divider()
    st.subheader(f"✏️ Edit expense ID {editing_id}")

    expense = load_one_expense(editing_id)

    if not expense or "error" in expense:
        st.error("Could not find that expense.")
        st.session_state.pop("editing_expense_id", None)

    else:
        categories = [
            "Food", "Transport", "Shopping", "Bills",
            "Health", "Education", "Entertainment", "Other",
        ]

        existing_category = expense["category"]

        if existing_category not in categories:
            categories.append(existing_category)

        with st.form(f"edit_form_{editing_id}"):
            edited_amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                value=float(expense["amount"]),
                step=10.0,
            )

            edited_category = st.selectbox(
                "Category",
                categories,
                index=categories.index(existing_category),
            )

            edited_description = st.text_input(
                "Description",
                value=expense.get("description", ""),
            )

            edited_date = st.date_input(
                "Expense date",
                value=date.fromisoformat(expense["expense_date"]),
            )

            save_edit = st.form_submit_button("Save changes")

            if save_edit:
                result = call_mcp_tool(
                    "update_expense",
                    {
                        "expense_id": int(editing_id),
                        "amount": float(edited_amount),
                        "category": edited_category,
                        "description": edited_description,
                        "expense_date": edited_date.isoformat(),
                    },
                )

                st.success(str(unwrap_result(result)))
                st.session_state.pop("editing_expense_id", None)
                st.rerun()

        if st.button("Cancel edit"):
            st.session_state.pop("editing_expense_id", None)
            st.rerun()


# ==========================================================
# DELETE CONFIRMATION
# ==========================================================

delete_id = st.session_state.get("confirm_delete_id")

if delete_id is not None:
    st.warning(f"Confirm deleting expense ID {delete_id}?")

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button("Confirm delete", type="primary"):
            result = call_mcp_tool(
                "delete_expense",
                {"expense_id": int(delete_id)},
            )

            st.success(str(unwrap_result(result)))
            st.session_state.pop("confirm_delete_id", None)
            st.rerun()

    with cancel_col:
        if st.button("Cancel delete"):
            st.session_state.pop("confirm_delete_id", None)
            st.rerun()


# ==========================================================
# MONTHLY SPENDING DASHBOARD - AUTOMATIC
# ==========================================================

st.divider()
st.header("📊 Monthly spending")

today = date.today()
month_name = today.strftime("%B %Y")

monthly_budget = st.number_input(
    "Monthly budget (₹)",
    min_value=1.0,
    value=6000.0,
    step=500.0,
    key="monthly_budget",
)

try:
    total_result = call_mcp_tool(
        "monthly_total",
        {
            "year": today.year,
            "month": today.month,
        },
    )

    monthly_total = parse_rupee_amount(total_result)

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric("Spent this month", f"₹{monthly_total:,.2f}")
    metric2.metric(
        "Budget remaining",
        f"₹{monthly_budget - monthly_total:,.2f}",
    )
    metric3.metric(
        "Budget used",
        f"{monthly_total / monthly_budget * 100:.1f}%",
    )

    st.subheader("💳 Monthly budget progress")

    st.progress(min(monthly_total / monthly_budget, 1.0))

    if monthly_total > monthly_budget:
        st.warning(
            f"You are ₹{monthly_total - monthly_budget:,.2f} over budget."
        )
    else:
        st.caption(
            f"₹{monthly_total:,.2f} spent out of "
            f"₹{monthly_budget:,.2f} for {month_name}."
        )

    category_result = call_mcp_tool(
        "top_categories",
        {
            "year": today.year,
            "month": today.month,
        },
    )

    category_rows = parse_category_totals(category_result)

    st.subheader("📈 Spending by category")

    if category_rows:
        category_df = pd.DataFrame(category_rows)

        st.bar_chart(
            category_df,
            x="Category",
            y="Amount (₹)",
            use_container_width=True,
        )

        with st.expander("View category details"):
            st.dataframe(
                category_df,
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.info("No expenses recorded for this month yet.")

except Exception as error:
    st.error(f"Could not load monthly spending: {error}")


# ==========================================================
# AI CHAT ASSISTANT
# ==========================================================

st.divider()
st.header("🤖 Chat with your expense assistant")

st.caption(
    "Ask about your expenses or request help managing them. "
    "For deletion, use the expense table's confirmation control."
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Show previous chat messages.
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input(
    "Ask something, e.g. 'What did I spend this month?'"
)

if user_prompt:
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response_text = run_ai_chat(user_prompt)
                st.markdown(response_text)

            except Exception as error:
                response_text = (
                    "Sorry, I couldn't complete that request. "
                    f"Error: {error}"
                )

                st.error(response_text)

    # Refresh dashboard/table after successful chat tool activity.
    st.rerun()