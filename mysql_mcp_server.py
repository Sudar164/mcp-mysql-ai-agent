
import os
import logging
import sqlglot
from sqlglot import exp

import mysql.connector
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

# Send diagnostic logs to stderr, not stdout.
# stdout is reserved for MCP communication over stdio.
logging.basicConfig(level=logging.INFO)

mcp = MCPServer("Marketing Sales MySQL Server")


def get_db_connection():
    """Create a connection to our MySQL database."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv(
            "MYSQL_DATABASE",
            "marketing_sales_db"
        ),
        connection_timeout=10,
    )


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the marketing and sales database."""
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")

        tables = [row[0] for row in cursor.fetchall()]

        return tables

    except mysql.connector.Error:
        logging.exception("Failed to retrieve database tables")
        raise RuntimeError(
            "Unable to retrieve tables from the MySQL database."
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@mcp.tool()
def get_database_schema() -> str:
    """Get table names, columns, data types, and foreign-key relationships."""

    connection = None
    cursor = None

    try:
        database_name = os.getenv(
            "MYSQL_DATABASE",
            "marketing_sales_db"
        )

        connection = get_db_connection()
        cursor = connection.cursor()

        # Get column details for every table
        cursor.execute(
            """
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_KEY
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
            (database_name,)
        )

        columns = cursor.fetchall()

        # Organize the columns by table
        schema_details = {}

        for table, column, data_type, nullable, key in columns:
            if table not in schema_details:
                schema_details[table] = []

            column_details = (
                f"  - {column} ({data_type}, "
                f"nullable={nullable}, key={key or 'None'})"
            )

            schema_details[table].append(column_details)

        # Get foreign-key relationships
        cursor.execute(
            """
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME, COLUMN_NAME
            """,
            (database_name,)
        )

        relationships = cursor.fetchall()

        # Build a readable schema description
        output = ["DATABASE SCHEMA", ""]

        for table, table_columns in schema_details.items():
            output.append(f"Table: {table}")
            output.extend(table_columns)
            output.append("")

        output.append("FOREIGN-KEY RELATIONSHIPS")

        if relationships:
            for table, column, ref_table, ref_column in relationships:
                output.append(
                    f"- {table}.{column} -> "
                    f"{ref_table}.{ref_column}"
                )
        else:
            output.append("No foreign-key relationships found.")

        return "\n".join(output)

    except mysql.connector.Error:
        logging.exception("Failed to retrieve database schema")
        raise RuntimeError(
            "Unable to retrieve the database schema."
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@mcp.tool()
def execute_readonly_query(sql_query: str) -> str:
    """Validate and execute a read-only SQL query against MySQL."""

    connection = None
    cursor = None

    try:
        # Step 1: Parse the SQL query
        statements = sqlglot.parse(
            sql_query,
            read="mysql"
        )

        # Step 2: Validate the query
        if not statements or len(statements) != 1:
            return "Error: Only one SQL statement is allowed."

        parsed_query = statements[0]

        if parsed_query is None:
            return "Error: Invalid SQL query."

        # Allow only SELECT statements
        if not isinstance(parsed_query, exp.Select):
            return "Error: Only SELECT queries are allowed."

        # Step 3: Connect to MySQL
        connection = get_db_connection()

        # Set query execution timeout to 10 seconds
        # cursor.execute("SET SESSION MAX_EXECUTION_TIME = 10000")

        cursor = connection.cursor()

        # Step 4: Execute the query
        cursor.execute(sql_query)

        # Step 5: Retrieve the results
        rows = cursor.fetchall()

        # Step 6: Get column names
        column_names = [
            description[0]
            for description in cursor.description
        ]

        # Step 7: Format the results
        output = []

        output.append("Query Results:")
        output.append(str(column_names))

        for row in rows:
            output.append(str(row))

        if not rows:
            output.append("No records found.")

        return "\n".join(output)

    except sqlglot.errors.ParseError:
        return "Error: Invalid SQL syntax."

    except mysql.connector.Error:
        logging.exception("SQL query execution failed")
        return "Error: Unable to execute the SQL query."

    except Exception:
        logging.exception("Unexpected error during query execution")
        return "Error: An unexpected error occurred."

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    mcp.run()
