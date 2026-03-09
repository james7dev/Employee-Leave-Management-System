from datetime import date, timedelta
from typing import List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _get_holidays() -> set:
    """Load public holidays from DB as a set of date strings."""
    try:
        from db.database import get_connection
        conn = get_connection()
        rows = conn.execute("SELECT date FROM public_holidays").fetchall()
        conn.close()
        return {r["date"] for r in rows}
    except Exception:
        return set()


def is_working_day(d: date, holidays: set = None) -> bool:
    if holidays is None:
        holidays = _get_holidays()
    return d.weekday() < 5 and d.strftime("%Y-%m-%d") not in holidays


def count_working_days(start_str: str, end_str: str) -> float:
    start = date.fromisoformat(start_str)
    end   = date.fromisoformat(end_str)
    if end < start:
        return 0
    holidays = _get_holidays()
    count = 0
    current = start
    while current <= end:
        if is_working_day(current, holidays):
            count += 1
        current += timedelta(days=1)
    return float(count)


def get_date_range(start_str: str, end_str: str) -> List[str]:
    start = date.fromisoformat(start_str)
    end   = date.fromisoformat(end_str)
    result = []
    current = start
    while current <= end:
        result.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return result


def get_working_days_in_range(start_str: str, end_str: str) -> List[str]:
    holidays = _get_holidays()
    return [
        d for d in get_date_range(start_str, end_str)
        if is_working_day(date.fromisoformat(d), holidays)
    ]


if __name__ == "__main__":
    print(count_working_days("2025-01-01", "2025-01-10"))  # Expected: 7
