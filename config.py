import os
from datetime import datetime

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "lms.db")

# App
CURRENT_YEAR = datetime.now().year
APP_NAME = "LeaveFlow"

# Default leave types: name -> (max_days, requires_approval, requires_docs, is_paid)
DEFAULT_LEAVE_TYPES = [
    ("Annual Leave",            20, True,  False, True),
    ("Sick Leave",              14, True,  False, True),
    ("Maternity/Paternity Leave",90, True,  True,  True),
    ("Emergency Leave",          5, True,  False, True),
    ("Unpaid Leave",            30, True,  False, False),
]

# Default HR admin account
DEFAULT_HR = {
    "name":       "HR Administrator",
    "email":      "hr@company.com",
    "password":   "admin123",
    "role":       "hr",
    "department": "Human Resources",
}

# Status values
STATUS_PENDING   = "Pending"
STATUS_APPROVED  = "Approved"
STATUS_REJECTED  = "Rejected"
STATUS_CANCELLED = "Cancelled"

ROLES = ["employee", "manager", "hr"]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Finance",
    "Human Resources", "Operations", "Product", "Design",
]
