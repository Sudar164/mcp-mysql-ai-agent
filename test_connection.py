
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

connection = None

try:
    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )

    if connection.is_connected():
        print("MySQL connection successful!")

        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print("Tables found in marketing_sales_db:")

        for table in tables:
            print("-", table[0])

        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]

        print(f"Total sales records: {sales_count}")

        cursor.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:", error)

finally:
    if connection is not None and connection.is_connected():
        connection.close()
        print("Connection closed.")
