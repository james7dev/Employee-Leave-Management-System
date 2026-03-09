import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from db.database import get_connection
from utils.date_utils import count_working_days
from utils.notifications import send_notification
from config import STATUS_PENDING_MANAGER, STATUS_APPROVED, CURRENT_YEAR


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

    # Fetch Leave Type Rules
    conn = get_connection()
    lt = conn.execute("SELECT * FROM leave_types WHERE id=?", (leave_type_id,)).fetchone()
    if not lt:
        conn.close()
        return False, "Leave type not found."
    
    # Notice Period Validation
    notice_period = lt["notice_period_days"]
    days_until_start = (start - date.today()).days
    if days_until_start < notice_period:
        conn.close()
        return False, f"Notice period for {lt['name']} is {notice_period} days. You only gave {days_until_start} days."

    working_days = count_working_days(start_str, end_str)
    if is_half_day:
        working_days = 0.5
    
    if working_days <= 0:
        conn.close()
        return False, "No working days in the selected range."

    # Max Consecutive Days Validation
    max_days = lt["max_consecutive_days"]
    if max_days and working_days > max_days:
        conn.close()
        return False, f"Maximum consecutive days for {lt['name']} is {max_days}. Requested: {working_days}."

    # Check balance
    bal = conn.execute(
        """SELECT total_days - used_days as remaining FROM leave_balances
           WHERE user_id=? AND leave_type_id=? AND year=?""",
        (employee_id, leave_type_id, start.year),
    ).fetchone()

    if bal is None:
        conn.close()
        return False, "No leave balance found for this leave type for the selected year."
    
    if bal["remaining"] < working_days:
        conn.close()
        return False, f"Insufficient balance. You have {bal['remaining']:.1f} days remaining."

    # Check Overlap
    overlap = conn.execute(
        """SELECT id FROM leave_requests 
           WHERE employee_id = ? 
           AND status IN ('Approved','Pending Manager','Pending HR','More Info Required')
           AND (start_date <= ? AND end_date >= ?)""",
        (employee_id, end_str, start_str)
    ).fetchone()
    
    if overlap:
        conn.close()
        return False, "You already have a leave request overlapping with this period."

    conn.close()
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
           (employee_id, leave_type_id, start_date, end_date, working_days, is_half_day, reason, status)
           VALUES (?,?,?,?,?,?,?,?)""",
        (employee_id, leave_type_id, start_str, end_str, working_days, int(is_half_day), reason, STATUS_PENDING_MANAGER),
    )
    request_id = cur.lastrowid

    if attachment_path:
        conn.execute(
            "INSERT INTO leave_documents (leave_request_id, file_path) VALUES (?,?)",
            (request_id, attachment_path)
        )

    # Fetch notification data before closing
    emp_row = conn.execute("SELECT manager_id, name FROM users WHERE id=?", (employee_id,)).fetchone()
    lt_name_row = conn.execute("SELECT name FROM leave_types WHERE id=?", (leave_type_id,)).fetchone()
    conn.commit()
    conn.close()

    # Notify manager
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
           WHERE u.manager_id=? AND lr.status IN (?, ?)
           ORDER BY lr.submitted_at ASC""",
        (manager_id, STATUS_PENDING_MANAGER, "More Info Required"),
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


def get_request_approvals(request_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT la.*, u.name as approver_name
           FROM leave_approvals la
           JOIN users u ON u.id = la.approver_id
           WHERE la.leave_request_id = ?
           ORDER BY la.timestamp ASC""",
        (request_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_request_documents(request_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM leave_documents WHERE leave_request_id = ?",
        (request_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
