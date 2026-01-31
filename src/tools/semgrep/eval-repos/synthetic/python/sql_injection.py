"""
Test file for SQL injection vulnerability detection.
Contains multiple SQL injection patterns.
"""

import sqlite3


def get_user_by_name(db: sqlite3.Connection, username: str) -> dict:
    """SQL INJECTION: String formatting in SQL query."""
    cursor = db.cursor()
    # SQL injection vulnerability - string formatting
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()


def search_products(db: sqlite3.Connection, search_term: str) -> list:
    """SQL INJECTION: String concatenation in SQL query."""
    cursor = db.cursor()
    # SQL injection vulnerability - concatenation
    query = "SELECT * FROM products WHERE name LIKE '%" + search_term + "%'"
    cursor.execute(query)
    return cursor.fetchall()


def delete_user(db: sqlite3.Connection, user_id: str) -> None:
    """SQL INJECTION: Format string with % operator."""
    cursor = db.cursor()
    # SQL injection vulnerability - % formatting
    query = "DELETE FROM users WHERE id = %s" % user_id
    cursor.execute(query)


def update_email(db: sqlite3.Connection, user_id: int, email: str) -> None:
    """SQL INJECTION: Multiple string formatting."""
    cursor = db.cursor()
    # SQL injection vulnerability - multiple user inputs
    query = f"UPDATE users SET email = '{email}' WHERE id = {user_id}"
    cursor.execute(query)


def get_orders_by_date(db: sqlite3.Connection, start_date: str, end_date: str) -> list:
    """SQL INJECTION: Multiple injectable parameters."""
    cursor = db.cursor()
    # SQL injection vulnerability
    query = "SELECT * FROM orders WHERE created_at BETWEEN '{}' AND '{}'".format(
        start_date, end_date
    )
    cursor.execute(query)
    return cursor.fetchall()


# SAFE example for comparison
def safe_get_user(db: sqlite3.Connection, user_id: int) -> dict:
    """SAFE: Uses parameterized query."""
    cursor = db.cursor()
    # Proper parameterized query - NOT a vulnerability
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()
