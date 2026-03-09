import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.person import Person
from db.database import get_connection
from config import CURRENT_YEAR, STATUS_PENDING, STATUS_CANCELLED


class Employee(Person):
    def __init__(self, id, name, email, department, role, manager_id=None):
        super().__init__(id, name, email, department, role)
        self.manager_id = manager_id

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"], name=row["name"], email=row["email"],
            department=row["department"], role=row["role"],
            manager_id=row.get("manager_id"),
        )

    # ── Balances ─────────────────────────────────────────────────────────────
    def get_balances(self, year: int = CURRENT_YEAR) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT lb.*, lt.name as leave_type_name, lt.is_paid
               FROM leave_balances lb
               JOIN leave_types lt ON lt.id = lb.leave_type_id
               WHERE lb.user_id=? AND lb.year=?""",
            (self.id, year),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_balance(self, leave_type_id: int, year: int = CURRENT_YEAR) -> float:
        conn = get_connection()
        row = conn.execute(
            "SELECT total_days - used_days as remaining FROM leave_balances "
            "WHERE user_id=? AND leave_type_id=? AND year=?",
            (self.id, leave_type_id, year),
        ).fetchone()
        conn.close()
        return row["remaining"] if row else 0.0

    # ── Requests ──────────────────────────────────────────────────────────────
    def get_history(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT lr.*, lt.name as leave_type_name, u.name as employee_name
               FROM leave_requests lr
               JOIN leave_types lt ON lt.id = lr.leave_type_id
               JOIN users u ON u.id = lr.employee_id
               WHERE lr.employee_id=?
               ORDER BY lr.submitted_at DESC""",
            (self.id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def cancel_request(self, request_id: int) -> tuple:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM leave_requests WHERE id=? AND employee_id=?",
            (request_id, self.id),
        ).fetchone()
        if not row:
            conn.close()
            return False, "Request not found."
        if row["status"] != STATUS_PENDING:
            conn.close()
            return False, f"Cannot cancel a request with status '{row['status']}'."
        conn.execute(
            "UPDATE leave_requests SET status=? WHERE id=?",
            (STATUS_CANCELLED, request_id),
        )
        conn.commit()
        conn.close()
        return True, "Request cancelled."


if __name__ == "__main__":
    emp = Employee(1, "Alice", "alice@co.com", "Engineering", "employee", manager_id=2)
    print(emp)
