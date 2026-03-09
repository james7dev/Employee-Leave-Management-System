import hashlib
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import get_connection


def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def login(email: str, password: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email=? AND is_active=1", (email,)
    ).fetchone()
    conn.close()
    if row and row["password"] == hash_password(password):
        return dict(row)
    return None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_managers() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, department FROM users WHERE role IN ('manager','hr') AND is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def change_password(user_id: int, new_password: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password=? WHERE id=?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
    conn.close()
