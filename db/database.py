import sqlite3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import DB_PATH, DEFAULT_LEAVE_TYPES, DEFAULT_HR, CURRENT_YEAR

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    seed_data()


def seed_data():
    conn = get_connection()

    # Seed leave types
    for name, max_days, req_approval, req_docs, is_paid in DEFAULT_LEAVE_TYPES:
        conn.execute(
            """INSERT OR IGNORE INTO leave_types
               (name, max_days_per_year, requires_approval, requires_docs, is_paid)
               VALUES (?,?,?,?,?)""",
            (name, max_days, int(req_approval), int(req_docs), int(is_paid)),
        )

    # Seed HR admin
    from services.auth_service import hash_password
    existing = conn.execute(
        "SELECT id FROM users WHERE email=?", (DEFAULT_HR["email"],)
    ).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO users (name, email, password, role, department)
               VALUES (?,?,?,?,?)""",
            (
                DEFAULT_HR["name"],
                DEFAULT_HR["email"],
                hash_password(DEFAULT_HR["password"]),
                DEFAULT_HR["role"],
                DEFAULT_HR["department"],
            ),
        )

    conn.commit()
    conn.close()


def provision_balances_for_user(user_id: int, year: int = CURRENT_YEAR):
    """Create leave balance rows for a newly created user."""
    conn = get_connection()
    leave_types = conn.execute("SELECT id, max_days_per_year FROM leave_types").fetchall()
    for lt in leave_types:
        conn.execute(
            """INSERT OR IGNORE INTO leave_balances (user_id, leave_type_id, year, total_days, used_days)
               VALUES (?,?,?,?,0)""",
            (user_id, lt["id"], year, lt["max_days_per_year"]),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    print("Tables created:", [t["name"] for t in tables])
    conn.close()
