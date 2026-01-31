"""Python file with resource management issues for testing F2_MISSING_USING detection."""

import sqlite3


def read_file_without_with(filename: str) -> str:
    """Bad: Opens file without using context manager."""
    # F2_MISSING_USING: file not opened with 'with'
    f = open(filename, 'r')
    content = f.read()
    f.close()  # Manual close - easy to forget
    return content


def process_multiple_files(files: list[str]) -> dict:
    """Bad: Multiple files opened without context managers."""
    results = {}
    for fname in files:
        # F2_MISSING_USING: each open needs 'with'
        handle = open(fname)
        results[fname] = handle.read()
        handle.close()
    return results


def database_without_context(db_path: str) -> list:
    """Bad: Database connection without context manager."""
    # F2_MISSING_USING: connection should use 'with'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    conn.close()
    return results


def correct_file_handling(filename: str) -> str:
    """Good: Proper context manager usage."""
    with open(filename, 'r') as f:
        return f.read()


def correct_database_handling(db_path: str) -> list:
    """Good: Proper context manager for database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()
