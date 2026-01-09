import pyodbc

conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=SRMUMATBU10;"
    "Database=YEDP2024;"
    "Trusted_Connection=yes;"
)

def get_connection():
    return pyodbc.connect(conn_str)