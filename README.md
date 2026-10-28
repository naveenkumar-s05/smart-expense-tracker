# Smart Expense Tracker

A personal expense tracking application built with Python, Streamlit, SQLite, and the Model Context Protocol (MCP).

## Features
- Add, view, update, and delete expenses with validation
- Store expense records in SQLite (existing records preserved)
- View recent and all expenses
- Persistent monthly budget configuration
- Monthly spending dashboard with category breakdown
- AI chat assistant with secure tool calling
- Comprehensive validation and error handling

## Technologies
- Python, Streamlit, SQLite, MCP, OpenRouter API, Pandas

## Setup (Windows PowerShell)
1. Clone repo and cd into directory
2. Create venv: `python -m venv venv; .\venv\Scripts\Activate.ps1`
3. Install deps: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`
5. Run: `streamlit run app.py`

## Testing
Run tests with temporary databases (no changes to production data):
```powershell
$env:PYTHONPATH="."; python -c "import unittest; loader=unittest.TestLoader(); suite=loader.discover('tests'); unittest.TextTestRunner(verbosity=2).run(suite)"
```

## Security
- API keys in .env only
- Parameterized SQL queries
- Input validation
- Explicit tool allowlist
- No secrets logged

## Notes
- Backups created: server_backup_before_improvements.py, app_backup_before_improvements.py, expenses_backup_before_improvements.db
- Budget persisted in config.db
- Existing expense records are unchanged
