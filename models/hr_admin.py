import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.person import Person
from db.database import get_connection, provision_balances_for_user
from config import CURRENT_YEAR


class HRAdmin(Person):

    def create_user(self, name, email, plain_password, role, department, manager_id=None) -> tuple:
        from services.auth_service import hash_password
        conn = get_connection()
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            conn.close()
            return False, "Email already registered."
        try:
            cur = conn.execute(
                """INSERT INTO users (name, email, password, role, department, manager_id)
                   VALUES (?,?,?,?,?,?)""",
                (name, email, hash_password(plain_password), role, department, manager_id),
            )
            user_id = cur.lastrowid
            conn.commit()
            provision_balances_for_user(user_id)
            conn.close()
            return True, user_id
        except Exception as e:
            conn.close()
            return False, str(e)

    def deactivate_user(self, user_id: int) -> tuple:
        conn = get_connection()
        conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True, "User deactivated."

    def activate_user(self, user_id: int) -> tuple:
        conn = get_connection()
        conn.execute("UPDATE users SET is_active=1 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True, "User activated."

    def update_leave_type(self, leave_type_id: int, max_days: int,
                          requires_approval: bool, requires_docs: bool) -> tuple:
        conn = get_connection()
        conn.execute(
            """UPDATE leave_types SET max_days_per_year=?, requires_approval=?, requires_docs=?
               WHERE id=?""",
            (max_days, int(requires_approval), int(requires_docs), leave_type_id),
        )
        conn.commit()
        conn.close()
        return True, "Leave type updated."

    def reset_balances(self, year: int = CURRENT_YEAR) -> tuple:
        """Reset used_days to 0 and sync total_days from leave_type config."""
        conn = get_connection()
        conn.execute(
            """UPDATE leave_balances SET used_days=0,
               total_days=(SELECT max_days_per_year FROM leave_types WHERE id=leave_type_id)
               WHERE year=?""",
            (year,),
        )
        conn.commit()
        conn.close()
        return True, f"Balances reset for {year}."

    def get_all_requests(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT lr.*, lt.name as leave_type_name,
                      u.name as employee_name, u.department
               FROM leave_requests lr
               JOIN leave_types lt ON lt.id = lr.leave_type_id
               JOIN users u ON u.id = lr.employee_id
               ORDER BY lr.submitted_at DESC"""
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_holiday(self, date_str: str, name: str) -> tuple:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO public_holidays (date, name) VALUES (?,?)",
                (date_str, name),
            )
            conn.commit()
            conn.close()
            return True, "Holiday added."
        except Exception as e:
            conn.close()
            return False, str(e)

    def delete_holiday(self, holiday_id: int) -> tuple:
        conn = get_connection()
        conn.execute("DELETE FROM public_holidays WHERE id=?", (holiday_id,))
        conn.commit()
        conn.close()
        return True, "Holiday deleted."

    def get_holidays(self) -> list:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM public_holidays ORDER BY date").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_users(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            """SELECT u.*, m.name as manager_name
               FROM users u LEFT JOIN users m ON m.id = u.manager_id
               ORDER BY u.department, u.name"""
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
