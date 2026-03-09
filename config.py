import os
from datetime import datetime

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "lms.db")

# App
CURRENT_YEAR = datetime.now().year
APP_NAME = "LeaveFlow"

# Status values
STATUS_DRAFT              = "Draft"
STATUS_PENDING_MANAGER    = "Pending Manager"
STATUS_PENDING_HR         = "Pending HR"
STATUS_APPROVED           = "Approved"
STATUS_REJECTED           = "Rejected"
STATUS_CANCELLED          = "Cancelled"
STATUS_MORE_INFO_REQUIRED = "More Info Required"

# Default leave types: 
# (name, annual_quota, requires_hr, requires_document, max_consecutive_days, notice_period_days)
DEFAULT_LEAVE_TYPES = [
    ("Annual Leave",            25, False, False, 15, 7),
    ("Sick Leave",              10, False, True,  10, 0),
    ("Casual Leave",            10, False, False, 3,  1),
    ("Maternity Leave",         180,True,  True,  180,30),
    ("Paternity Leave",         14, True,  True,  14, 30),
    ("Unpaid Leave",            365,True,  False, 365,14),
    ("Compensatory Leave",      0,  False, False, 5,  1),
]

# Default HR admin account
DEFAULT_HR = {
    "name":       "HR Administrator",
    "email":      "hr@company.com",
    "password":   "admin123",
    "role":       "hr",
    "department": "Human Resources",
}

ROLES = ["employee", "manager", "hr", "admin"]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Finance",
    "Human Resources", "Operations", "Product", "Design",
]
