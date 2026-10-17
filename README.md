
# Smart Expense Tracker with AI Chat

A personal expense tracking application built with **Python, Streamlit, SQLite, and the Model Context Protocol (MCP)**. It helps users record expenses, manage a monthly budget, view spending summaries, and ask an AI assistant questions about their expenses.

## Features

- **Add, view, update, and delete expenses**
- Store expense records in a local SQLite database
- View recent expenses and browse all recorded expenses
- Track monthly spending against a budget
- View remaining budget and spending progress
- Visualize spending by category
- Ask the AI assistant questions about expense records
- Use MCP tools to let the AI interact with expense data

## Technologies Used

- Python
- Streamlit
- SQLite
- Model Context Protocol (MCP)
- OpenRouter API
- OpenAI-compatible Python client
- Pandas

## Project Structure

```text
smart-expense-tracker/
├── app.py              # Streamlit application and AI chat interface
├── server.py           # MCP server and expense management tools
├── expenses.db         # Local SQLite database (created by the app)
├── .env                # API key and configuration (keep private)
├── .gitignore
└── README.md
```

> The database and `.env` file are local files. Do not commit private expense data or API keys to GitHub.

## Requirements

- Python 3.10 or newer
- An OpenRouter API key for AI chat
- Internet access for OpenRouter-powered AI responses

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Replace the URL with your GitHub repository URL.

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the packages your project uses. If you have a `requirements.txt` file, run:

```powershell
pip install -r requirements.txt
```

If you do not have one yet, create it from your working environment:

```powershell
pip freeze > requirements.txt
```

### 4. Configure your API key

Create a `.env` file in the project root and add your OpenRouter key using the variable name expected by your application.

For example, if your code reads `OPENROUTER_API_KEY`:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Never share or commit your real API key. Check that `.env` is included in `.gitignore`.

### 5. Run the application

Start the Streamlit interface:

```powershell
streamlit run app.py
```

Streamlit will provide a local URL—usually `http://localhost:8501`—to open the application in your browser.

## Example AI Chat Prompts

Try asking the AI assistant:

- “Add an expense of ₹120 for Travel, description bus fare, today.”
- “Show my recent expenses.”
- “Update the Travel expense to ₹150.”
- “How much have I spent this month?”
- “Which category did I spend the most on?”
- “How much of my monthly budget is remaining?”

## How It Works

1. The user records and manages expenses through the Streamlit interface.
2. Expense information is stored in a local SQLite database.
3. The MCP server exposes expense operations as tools.
4. The AI chat uses OpenRouter to understand the user's request and can call the available MCP tools.
5. The dashboard displays expense records, monthly budget information, and category-wise spending.

## Security Notes

- Keep API keys in `.env`; never commit them to GitHub.
- Keep `.env`, virtual environment folders, and private database files out of version control.
- Use sample data when demonstrating the project publicly.
- Review AI tool permissions before enabling actions that modify or delete records.

## Future Improvements

- Export expense reports to CSV or PDF
- Add charts for spending trends across multiple months
- Add user authentication and separate accounts
- Add recurring expenses and expense reminders
- Improve AI responses with budget-aware recommendations

## Author

**Naveen Kumar S**

GitHub: [naveenkumar-s05](https://github.com/naveenkumar-s05)

Project Repository: [Smart Expense Tracker](https://github.com/naveenkumar-s05/smart-expense-tracker)