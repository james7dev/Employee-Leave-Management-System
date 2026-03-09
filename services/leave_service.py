import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from db.database import get_connection
from utils.date_utils import count_working_days
from utils.notifications import send_notification
from config import STATUS_PENDING, STATUS_APPROVED, CURRENT_YEAR


def get_leave_types() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM leave_types ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def validate_request(employee_id: int, leave_type_id: int,
                     start_str: str, end_str: str, is_half_day: bool = False) -> tuple:
    try:
        start = date.fromisoformat(start_str)
        end   = date.fromisoformat(end_str)
    except ValueError:
        return False, "Invalid date format."

    if end < start:
        return False, "End date must be on or after start date."
    if start < date.today():
        return False, "Start date cannot be in the past."

    working_days = count_working_days(start_str, end_str)
    if is_half_day:
        working_days = 0.5
    if working_days <= 0:
        return False, "No working days in the selected range."

    # Check balance
    conn = get_connection()
    bal = conn.execute(
        """SELECT total_days - used_days as remaining FROM leave_balances
           WHERE user_id=? AND leave_type_id=? AND year=strftime('%Y','now')""",
        (employee_id, leave_type_id),
    ).fetchone()
    conn.close()

    if bal is None:
        return False, "No leave balance found for this leave type."
    if bal["remaining"] < working_days:
        return False, f"Insufficient balance. You have {bal['remaining']:.1f} days remaining."

    return True, working_days


def submit_leave(employee_id: int, leave_type_id: int,
                 start_str: str, end_str: str,
                 reason: str = "", is_half_day: bool = False,
                 attachment_path: str = None) -> tuple:
    ok, result = validate_request(employee_id, leave_type_id, start_str, end_str, is_half_day)
    if not ok:
        return False, result
    working_days = result

    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO leave_requests
           (employee_id, leave_type_id, start_date, end_date, working_days, is_half_day, reason, attachment_path)
           VALUES (?,?,?,?,?,?,?,?)""",
        (employee_id, leave_type_id, start_str, end_str, working_days, int(is_half_day), reason, attachment_path),
    )
    request_id = cur.lastrowid

    # Fetch notification data before closing
    emp_row = conn.execute("SELECT manager_id, name FROM users WHERE id=?", (employee_id,)).fetchone()
    lt_name_row = conn.execute("SELECT name FROM leave_types WHERE id=?", (leave_type_id,)).fetchone()
    conn.commit()
    conn.close()

    # Notify manager (separate connection)
    if emp_row and emp_row["manager_id"] and lt_name_row:
        send_notification(
            emp_row["manager_id"],
            f"📋 {emp_row['name']} submitted a {lt_name_row['name']} request ({start_str} → {end_str}).",
        )
    return True, request_id


def check_conflict(employee_id: int, start_str: str, end_str: str) -> list:
    conn = get_connection()
    emp = conn.execute("SELECT manager_id FROM users WHERE id=?", (employee_id,)).fetchone()
    if not emp or not emp["manager_id"]:
        conn.close()
        return []
    rows = conn.execute(
        """SELECT u.name, lr.start_date, lr.end_date
           FROM leave_requests lr
           JOIN users u ON u.id = lr.employee_id
           WHERE u.manager_id=? AND lr.employee_id != ?
             AND lr.status=? AND lr.start_date <= ? AND lr.end_date >= ?""",
        (emp["manager_id"], employee_id, STATUS_APPROVED, end_str, start_str),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_requests_for_manager(manager_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT lr.*, lt.name as leave_type_name,
                  u.name as employee_name, u.department
           FROM leave_requests lr
           JOIN leave_types lt ON lt.id = lr.leave_type_id
           JOIN users u ON u.id = lr.employee_id
           WHERE u.manager_id=? AND lr.status=?
           ORDER BY lr.submitted_at ASC""",
        (manager_id, STATUS_PENDING),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_employee_requests(employee_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT lr.*, lt.name as leave_type_name
           FROM leave_requests lr
           JOIN leave_types lt ON lt.id = lr.leave_type_id
           WHERE lr.employee_id=?
           ORDER BY lr.submitted_at DESC""",
        (employee_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_team_calendar(manager_id: int) -> list:
    """Return approved leave rows for a manager's team."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT lr.*, u.name as employee_name, lt.name as leave_type_name
           FROM leave_requests lr
           JOIN users u ON u.id = lr.employee_id
           JOIN leave_types lt ON lt.id = lr.leave_type_id
           WHERE u.manager_id=? AND lr.status=?
           ORDER BY lr.start_date""",
        (manager_id, STATUS_APPROVED),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def accrue_monthly(user_id: int, year: int = CURRENT_YEAR):
    """Add 1.67 days to Annual Leave balance (stretch: call monthly)."""
    conn = get_connection()
    annual = conn.execute(
        "SELECT id FROM leave_types WHERE name='Annual Leave'"
    ).fetchone()
    if annual:
        conn.execute(
            """UPDATE leave_balances SET total_days = total_days + 1.67
               WHERE user_id=? AND leave_type_id=? AND year=?""",
            (user_id, annual["id"], year),
        )
        conn.commit()
    conn.close()
