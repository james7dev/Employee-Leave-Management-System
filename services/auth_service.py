import hashlib
import secrets
import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import get_connection, provision_balances_for_user


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


def create_session(user_id: int, days: int = 7) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at)
    )
    conn.commit()
    conn.close()
    return token


def get_user_from_session(token: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        """SELECT u.* FROM users u 
           JOIN sessions s ON u.id = s.user_id 
           WHERE s.token = ? AND s.expires_at > ? AND u.is_active = 1""",
        (token, datetime.datetime.now().isoformat())
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(token: str):
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


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


def register_user(name: str, email: str, password: str, role: str, department: str, manager_id: int = None) -> tuple:
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        conn.close()
        return False, "Email already registered."
    try:
        cur = conn.execute(
            """INSERT INTO users (name, email, password, role, department, manager_id)
               VALUES (?,?,?,?,?,?)""",
            (name, email, hash_password(password), role, department, manager_id),
        )
        user_id = cur.lastrowid
        conn.commit()
        provision_balances_for_user(user_id)
        conn.close()
        return True, user_id
    except Exception as e:
        conn.close()
        return False, str(e)
