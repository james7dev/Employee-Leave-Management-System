"""
CLI integration test — run with:  python test_flow.py
Tests the full flow: seed → employee submit → manager approve → balance deducted
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from db.database import init_db, provision_balances_for_user
from services.auth_service import login, hash_password
from services.leave_service import submit_leave, get_employee_requests
from models.employee import Employee
from models.manager import Manager
from models.hr_admin import HRAdmin
from db.database import get_connection

print("=" * 60)
print("LeaveFlow — Integration Test")
print("=" * 60)

# 1. Init DB
print("\n[1] Initialising database...")
init_db()
print("    ✓ DB initialised")

# 2. Login as HR, create test users
print("\n[2] Creating test users via HRAdmin...")
hr_user = login("hr@company.com", "admin123")
assert hr_user, "HR login failed — check seed_data()"
hr = HRAdmin.from_row(hr_user)

ok, mgr_id = hr.create_user("Test Manager", "mgr@test.com", "pass123",
                              "manager", "Engineering")
if not ok:
    conn = get_connection()
    mgr_id = conn.execute("SELECT id FROM users WHERE email='mgr@test.com'").fetchone()["id"]
    conn.close()
print(f"    Manager ID: {mgr_id}")

ok, emp_id = hr.create_user("Test Employee", "emp@test.com", "pass123",
                              "employee", "Engineering", manager_id=mgr_id)
if not ok:
    conn = get_connection()
    emp_id = conn.execute("SELECT id FROM users WHERE email='emp@test.com'").fetchone()["id"]
    conn.close()
print(f"    Employee ID: {emp_id}")

# 3. Employee submits leave
print("\n[3] Employee submitting Annual Leave request...")
emp_user = login("emp@test.com", "pass123")
assert emp_user, "Employee login failed"
emp = Employee.from_row(emp_user)

from datetime import date, timedelta
today      = date.today()
start      = (today + timedelta(days=3)).strftime("%Y-%m-%d")
end        = (today + timedelta(days=7)).strftime("%Y-%m-%d")

conn = get_connection()
lt  = conn.execute("SELECT id FROM leave_types WHERE name='Annual Leave'").fetchone()
conn.close()

ok, result = submit_leave(emp.id, lt["id"], start, end, "Vacation trip")
assert ok, f"Submit failed: {result}"
request_id = result
print(f"    ✓ Request submitted (ID: {request_id}, {start} → {end})")

# 4. Check balance before approval
bal_before = emp.get_balance(lt["id"])
print(f"\n[4] Balance before approval: {bal_before} days")

# 5. Manager approves
print("\n[5] Manager approving request...")
mgr_user = login("mgr@test.com", "pass123")
assert mgr_user, "Manager login failed"
mgr = Manager.from_row(mgr_user)

ok, msg = mgr.approve_request(request_id, "Approved — enjoy!")
assert ok, f"Approve failed: {msg}"
print(f"    ✓ {msg}")

# 6. Check balance after approval
emp_user = login("emp@test.com", "pass123")
emp2 = Employee.from_row(emp_user)
bal_after = emp2.get_balance(lt["id"])
print(f"\n[6] Balance after approval: {bal_after} days")
assert bal_after < bal_before, "Balance was NOT deducted after approval!"
print(f"    ✓ Balance deducted by {bal_before - bal_after:.1f} days")

# 7. Verify request status
reqs = get_employee_requests(emp.id)
req  = next(r for r in reqs if r["id"] == request_id)
assert req["status"] == "Approved", f"Expected Approved, got {req['status']}"
print(f"\n[7] ✓ Request status: {req['status']}")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
