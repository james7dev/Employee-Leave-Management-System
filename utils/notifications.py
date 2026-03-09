import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import get_connection


def send_notification(user_id: int, message: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO notifications (user_id, message) VALUES (?,?)",
        (user_id, message),
    )
    conn.commit()
    conn.close()


def get_unread(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_notifications(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_read(notif_id: int):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notif_id,))
    conn.commit()
    conn.close()


def mark_all_read(user_id: int):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
