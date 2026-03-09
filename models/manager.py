import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.employee import Employee
from db.database import get_connection
from config import (
    STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING_MANAGER, 
    STATUS_PENDING_HR, STATUS_MORE_INFO_REQUIRED, CURRENT_YEAR
)
from utils.notifications import send_notification


class Manager(Employee):

    def get_team_requests(self, status: str = None) -> list:
        conn = get_connection()
        query = """
            SELECT lr.*, lt.name as leave_type_name, u.name as employee_name,
                   u.department
            FROM leave_requests lr
            JOIN leave_types lt ON lt.id = lr.leave_type_id
            JOIN users u ON u.id = lr.employee_id
            WHERE u.manager_id=?
        """
        params = [self.id]
        if status:
            query += " AND lr.status=?"
            params.append(status)
        query += " ORDER BY lr.submitted_at DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_team_members(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM users WHERE manager_id=? AND is_active=1", (self.id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def approve_request(self, request_id: int, note: str = "") -> tuple:
        conn = get_connection()
        row = conn.execute(
            """SELECT lr.*, u.manager_id, lt.requires_hr FROM leave_requests lr
               JOIN users u ON u.id = lr.employee_id
               JOIN leave_types lt ON lt.id = lr.leave_type_id
               WHERE lr.id=? AND u.manager_id=?""",
            (request_id, self.id),
        ).fetchone()
        
        if not row:
            conn.close()
            return False, "Request not found or not in your team."
        if row["status"] != STATUS_PENDING_MANAGER:
            conn.close()
            return False, f"Request is already '{row['status']}'."

        # All requests are now forwarded to HR as per user requirement
        new_status = STATUS_PENDING_HR
        msg = "Request forwarded to HR."

        conn.execute(
            """UPDATE leave_requests SET status=?, manager_id=?,
               updated_at=datetime('now') WHERE id=?""",
            (new_status, self.id, request_id),
        )
        
        # Log approval action
        conn.execute(
            """INSERT INTO leave_approvals (leave_request_id, approver_id, role, action, comment)
               VALUES (?,?,?,?,?)""",
            (request_id, self.id, "manager", "FORWARDED", note)
        )

        conn.commit()
        conn.close()
        
        send_notification(
            row["employee_id"],
            f"📋 Your leave request ({row['start_date']} → {row['end_date']}) status updated to: {new_status}.",
        )
        return True, msg

    def reject_request(self, request_id: int, note: str) -> tuple:
        if not note or not note.strip():
            return False, "A rejection note is required."
        conn = get_connection()
        row = conn.execute(
            """SELECT lr.*, u.manager_id FROM leave_requests lr
               JOIN users u ON u.id = lr.employee_id
               WHERE lr.id=? AND u.manager_id=?""",
            (request_id, self.id),
        ).fetchone()
        if not row:
            conn.close()
            return False, "Request not found or not in your team."
        if row["status"] != STATUS_PENDING_MANAGER:
            conn.close()
            return False, f"Request is already '{row['status']}'."
        
        conn.execute(
            """UPDATE leave_requests SET status=?, manager_id=?,
               updated_at=datetime('now') WHERE id=?""",
            (STATUS_REJECTED, self.id, request_id),
        )
        
        conn.execute(
            """INSERT INTO leave_approvals (leave_request_id, approver_id, role, action, comment)
               VALUES (?,?,?,?,?)""",
            (request_id, self.id, "manager", "REJECTED", note)
        )
        
        conn.commit()
        conn.close()
        send_notification(
            row["employee_id"],
            f"❌ Your leave request ({row['start_date']} → {row['end_date']}) was rejected by manager. Note: {note}",
        )
        return True, "Request rejected."

    def request_more_info(self, request_id: int, note: str) -> tuple:
        if not note or not note.strip():
            return False, "A comment is required to request more info."
        conn = get_connection()
        row = conn.execute(
            """SELECT lr.*, u.manager_id FROM leave_requests lr
               JOIN users u ON u.id = lr.employee_id
               WHERE lr.id=? AND u.manager_id=?""",
            (request_id, self.id),
        ).fetchone()
        if not row:
            conn.close()
            return False, "Request not found or not in your team."
        
        conn.execute(
            """UPDATE leave_requests SET status=?, updated_at=datetime('now') WHERE id=?""",
            (STATUS_MORE_INFO_REQUIRED, request_id),
        )
        
        conn.execute(
            """INSERT INTO leave_approvals (leave_request_id, approver_id, role, action, comment)
               VALUES (?,?,?,?,?)""",
            (request_id, self.id, "manager", "REQUEST_INFO", note)
        )
        
        conn.commit()
        conn.close()
        send_notification(
            row["employee_id"],
            f"ℹ️ More information required for your leave request ({row['start_date']}). Note: {note}",
        )
        return True, "More info requested."

    def check_team_conflict(self, start_date: str, end_date: str, exclude_employee_id: int = None) -> list:
        conn = get_connection()
        query = """
            SELECT u.name, lr.start_date, lr.end_date
            FROM leave_requests lr
            JOIN users u ON u.id = lr.employee_id
            WHERE u.manager_id=? AND lr.status=?
              AND lr.start_date <= ? AND lr.end_date >= ?
        """
        params = [self.id, STATUS_APPROVED, end_date, start_date]
        if exclude_employee_id:
            query += " AND u.id != ?"
            params.append(exclude_employee_id)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
