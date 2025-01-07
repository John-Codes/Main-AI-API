import sqlite3
from typing import Generator

DATABASE_URL = "test_database.db"

class DatabaseConnection:
    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection):
    try:
        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL
            )
        """)
        # Create monthly_goals table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_goals (
                user_id INTEGER PRIMARY KEY,
                goal TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise
