# MCP-Powered MySQL AI Agent

An AI-powered Marketing and Sales Data Analyst that allows users to interact with a MySQL database using natural language.

Built using **Python, Model Context Protocol (MCP), Groq API, MySQL, and Streamlit**.

## Project Overview

This project demonstrates how Large Language Models (LLMs) can interact with databases through the Model Context Protocol (MCP).

Instead of manually writing SQL queries, users can ask questions in plain English. The AI agent understands the question, generates the appropriate SQL query, executes it against the MySQL database through MCP tools, and returns the result in natural language.

### Example

**User:** Which product generated the highest revenue?

**AI Agent:** The product with the highest revenue is [Product Name], generating [Revenue].

## Architecture

```text
                 User
                   |
                   v
             Streamlit UI
                   |
                   v
              Groq LLM
                   |
             MCP Client
                   |
                   v
              MCP Server
                   |
          +--------+--------+
          |        |        |
          v        v        v
      List Tables  Get     Execute
                  Schema   Read-Only
                           SQL Query
                             |
                             v
                        MySQL Database
                             |
                             v
                       Query Results
                             |
                             v
                       Groq LLM
                             |
                             v
                    Natural Language
                         Response
```

## Key Features

- Natural language to SQL query generation.
- MCP-based communication between the AI agent and MySQL.
- Dynamic database schema inspection.
- Read-only SQL query execution.
- SQL query validation using SQLGlot.
- Secure database access using a dedicated read-only MySQL account.
- Marketing and sales analytics.
- Interactive Streamlit interface.
- Natural language responses instead of raw SQL output.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Groq API | LLM inference and SQL generation |
| MCP | Communication between AI and database tools |
| MySQL | Relational database |
| Streamlit | User interface |
| SQLGlot | SQL parsing and validation |
| mysql-connector-python | MySQL connectivity |
| python-dotenv | Environment variable management |

## Database Design

The project uses a marketing and sales database named `marketing_sales_db`.

The database contains five tables:

| Table | Description |
|---|---|
| campaigns | Marketing campaign details |
| products | Product information |
| customers | Customer details |
| leads | Marketing leads and their status |
| sales | Sales transactions and revenue details |

### Relationships

- Each lead belongs to a customer.
- Each lead is associated with a marketing campaign.
- Each sale is associated with a lead.
- Each sale references a product.

## Project Structure

```text
mcp-sql-agent/
│
├── mysql_mcp_server.py    # MCP server and MySQL tools
├── groq_agent.py          # Groq-powered MCP client agent
├── streamlit_app.py       # Streamlit user interface
├── test_connection.py     # MySQL connection testing
├── test_mcp_client.py     # MCP client testing
├── .gitignore             # Excluded files and secrets
├── .env                   # Local environment variables
└── README.md              # Project documentation
```

**Note:** The `.env` file is local and should never be committed to GitHub.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/mcp-mysql-ai-agent.git
```

Navigate into the project:

```bash
cd mcp-mysql-ai-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install groq mcp mysql-connector-python python-dotenv streamlit sqlglot
```

### 4. Configure environment variables

Create a `.env` file in the project root directory.

Add your own credentials:

```env
GROQ_API_KEY=your_groq_api_key

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_mysql_readonly_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=marketing_sales_db
```

Never upload your actual API key or database password to GitHub.

### 5. Configure MySQL

Install and start MySQL Server.

Create the `marketing_sales_db` database and configure the five required tables:

- campaigns
- products
- customers
- leads
- sales

Populate the tables with marketing and sales data.

Create a dedicated MySQL user with only the required `SELECT` permissions. Configure its credentials in `.env`.

### 6. Run the application

Start the Streamlit application:

```bash
streamlit run streamlit_app.py
```

The application will open in your browser.

## Example Questions

Try asking the AI agent:

1. Which product generated the highest revenue?
2. Which marketing channel generated the most leads?
3. Find the top three salespeople based on revenue.
4. Which campaign generated the highest revenue?
5. Which region has the most customers?
6. What about the second-highest product?
7. Show revenue generated in the West region.
8. What was the revenue in October 2026?
9. What is the average sale value?
10. Show me the best-performing campaign.

## Security Considerations

- Database credentials are stored in environment variables.
- API keys are not hardcoded into the application.
- A dedicated read-only MySQL account is used.
- SQL queries are parsed and validated before execution.
- Only read-only SELECT queries are intended to be executed.
- Query execution is subject to result limits and timeout controls.

**Important:** SQL validation is an additional safeguard, not a substitute for database-level permissions and production-grade security controls.

## Future Enhancements

- Conversational memory for follow-up questions.
- Multi-step reasoning across multiple database queries.
- Improved clarification handling for ambiguous questions.
- Support for additional databases.
- Query explanation and visualization.
- Advanced analytics and reporting.

## Author

**Sudaroli Gopal**

B.Tech Information Technoogy

AI & Data Engineer

---

*Built as a hands-on project to explore MCP, LLM integration, database interaction, and natural language analytics.*