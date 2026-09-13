import os
import sqlite3

# Define base project directory and database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "culinary.db")


def get_db():
    """Opens a database connection, configures Row factory, and enables FOREIGN KEY constraints."""
    conn = sqlite3.connect(DATABASE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_db(conn):
    """Closes an active database connection."""
    if conn:
        conn.close()