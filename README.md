# 🌿 LeaveFlow — Employee Leave Management System

A full-stack leave management system built with **pure Python**, **SQLite**, and **Streamlit**.

---

## Features

- **3 roles**: Employee, Manager, HR Admin
- Leave request submission with balance validation
- Manager approval / rejection workflow with notes
- Conflict detection (overlapping team leave)
- 30-day team calendar view
- HR reports with charts (Plotly)
- Notifications system
- CSV export
- Half-day leave support

---

## Quick Start

### 1. Install dependencies

```bash
pip install streamlit pandas plotly
```

### 2. Run the app

```bash
cd lms
streamlit run app.py
```

The database is created and seeded automatically on first run.

---

## Default Credentials

| Role       | Email               | Password  |
|------------|---------------------|-----------|
| HR Admin   | hr@company.com      | admin123  |

Create Manager and Employee accounts via the HR Admin dashboard.

---

## Project Structure

```
lms/
├── app.py                     # Streamlit entry point + routing
├── config.py                  # Constants and defaults
├── test_flow.py               # CLI integration test
├── db/
│   ├── database.py            # Connection, init, seed
│   └── schema.sql             # All CREATE TABLE statements
├── models/
│   ├── person.py              # Base class
│   ├── employee.py            # Employee (inherits Person)
│   ├── manager.py             # Manager (inherits Employee)
│   ├── hr_admin.py            # HRAdmin (inherits Person)
│   ├── leave_type.py          # LeaveType model
│   └── leave_request.py       # LeaveRequest model
├── services/
│   ├── auth_service.py        # Login, hashing, user lookup
│   ├── leave_service.py       # Core leave workflow logic
│   └── report_service.py      # HR reporting queries
├── pages/
│   ├── login.py               # Login page
│   ├── employee_dashboard.py  # Employee UI
│   ├── manager_dashboard.py   # Manager UI
│   └── hr_dashboard.py        # HR Admin UI
└── utils/
    ├── date_utils.py          # Working day calculations
    └── notifications.py       # Notification helpers
```

---

## Running the Integration Test

```bash
cd lms
python test_flow.py
```

This runs a full round-trip: create users → submit leave → manager approves → verify balance deducted.

---

## Leave Types (Defaults)

| Type                    | Days | Paid |
|-------------------------|------|------|
| Annual Leave            | 20   | ✅   |
| Sick Leave              | 14   | ✅   |
| Maternity/Paternity     | 90   | ✅   |
| Emergency Leave         | 5    | ✅   |
| Unpaid Leave            | 30   | ❌   |
