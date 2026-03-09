import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import get_connection
from config import CURRENT_YEAR


def get_leave_by_department(year: int = CURRENT_YEAR) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.department, lt.name as leave_type, SUM(lr.working_days) as total_days
           FROM leave_requests lr
           JOIN users u ON u.id = lr.employee_id
           JOIN leave_types lt ON lt.id = lr.leave_type_id
           WHERE lr.status='Approved' AND strftime('%Y', lr.start_date)=?
           GROUP BY u.department, lt.name
           ORDER BY u.department""",
        (str(year),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_leave_type_summary(year: int = CURRENT_YEAR) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT lt.name as leave_type, COUNT(*) as request_count,
                  SUM(lr.working_days) as total_days
           FROM leave_requests lr
           JOIN leave_types lt ON lt.id = lr.leave_type_id
           WHERE lr.status='Approved' AND strftime('%Y', lr.start_date)=?
           GROUP BY lt.name ORDER BY total_days DESC""",
        (str(year),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_absence_rate(year: int = CURRENT_YEAR) -> list:
    WORKING_DAYS_PER_YEAR = 260
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.name, u.department,
                  COALESCE(SUM(lr.working_days),0) as used_days
           FROM users u
           LEFT JOIN leave_requests lr ON lr.employee_id=u.id
               AND lr.status='Approved' AND strftime('%Y', lr.start_date)=?
           WHERE u.role='employee' AND u.is_active=1
           GROUP BY u.id ORDER BY used_days DESC""",
        (str(year),),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["absence_rate"] = round(d["used_days"] / WORKING_DAYS_PER_YEAR * 100, 1)
        result.append(d)
    return result


def get_monthly_trend(year: int = CURRENT_YEAR) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT strftime('%m', lr.start_date) as month,
                  SUM(lr.working_days) as total_days
           FROM leave_requests lr
           WHERE lr.status='Approved' AND strftime('%Y', lr.start_date)=?
           GROUP BY month ORDER BY month""",
        (str(year),),
    ).fetchall()
    conn.close()
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    return [{"month": month_names[int(r["month"])-1], "total_days": r["total_days"]}
            for r in rows]
