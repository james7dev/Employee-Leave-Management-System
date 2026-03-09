import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.employee import Employee
from db.database import get_connection
from config import STATUS_APPROVED, STATUS_REJECTED, STATUS_PENDING, CURRENT_YEAR
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
            """SELECT lr.*, u.manager_id FROM leave_requests lr
               JOIN users u ON u.id = lr.employee_id
               WHERE lr.id=? AND u.manager_id=?""",
            (request_id, self.id),
        ).fetchone()
        if not row:
            conn.close()
            return False, "Request not found or not in your team."
        if row["status"] != STATUS_PENDING:
            conn.close()
            return False, f"Request is already '{row['status']}'."

        # Deduct balance
        conn.execute(
            """UPDATE leave_balances
               SET used_days = used_days + ?
               WHERE user_id=? AND leave_type_id=? AND year=strftime('%Y', 'now')""",
            (row["working_days"], row["employee_id"], row["leave_type_id"]),
        )
        conn.execute(
            """UPDATE leave_requests SET status=?, manager_note=?,
               actioned_at=datetime('now') WHERE id=?""",
            (STATUS_APPROVED, note, request_id),
        )
        conn.commit()
        conn.close()
        send_notification(
            row["employee_id"],
            f"✅ Your leave request ({row['start_date']} → {row['end_date']}) was approved.",
        )
        return True, "Request approved."

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
        if row["status"] != STATUS_PENDING:
            conn.close()
            return False, f"Request is already '{row['status']}'."
        conn.execute(
            """UPDATE leave_requests SET status=?, manager_note=?,
               actioned_at=datetime('now') WHERE id=?""",
            (STATUS_REJECTED, note, request_id),
        )
        conn.commit()
        conn.close()
        send_notification(
            row["employee_id"],
            f"❌ Your leave request ({row['start_date']} → {row['end_date']}) was rejected. Note: {note}",
        )
        return True, "Request rejected."

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


if __name__ == "__main__":
    m = Manager(2, "Bob", "bob@co.com", "Engineering", "manager")
    print(m)
