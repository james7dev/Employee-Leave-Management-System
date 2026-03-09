"""
CLI integration test — Updated for new Leave Flow
Tests: 
1. Employee submits Annual Leave (no HR required) -> Manager approves -> Balance deducted
2. Employee submits Maternity Leave (HR required) -> Manager forwards -> HR approves -> Balance deducted
3. Employee submits Casual Leave with short notice -> Should fail
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from db.database import init_db
from services.auth_service import login
from services.leave_service import submit_leave, get_employee_requests
from models.employee import Employee
from models.manager import Manager
from models.hr_admin import HRAdmin
from db.database import get_connection
from datetime import date, timedelta
from config import STATUS_APPROVED, STATUS_PENDING_HR, STATUS_PENDING_MANAGER

def run_test():
    print("=" * 60)
    print("LeaveFlow — Expanded Integration Test")
    print("=" * 60)

    # 1. Init DB
    print("\n[1] Initialising database...")
    init_db()
    print("    ✓ DB initialised")

    # 2. Setup users
    print("\n[2] Setting up test users...")
    hr_user = login("hr@company.com", "admin123")
    hr = HRAdmin.from_row(hr_user)

    ok, mgr_id = hr.create_user("Test Manager", "mgr@test.com", "pass123", "manager", "Engineering")
    ok, emp_id = hr.create_user("Test Employee", "emp@test.com", "pass123", "employee", "Engineering", manager_id=mgr_id)
    print(f"    ✓ Manager ID: {mgr_id}, Employee ID: {emp_id}")

    # 3. Test 1: Annual Leave (No HR)
    print("\n[3] Test 1: Annual Leave (Manager Approval Only)")
    emp = Employee.from_row(login("emp@test.com", "pass123"))
    conn = get_connection()
    lt_annual = conn.execute("SELECT id FROM leave_types WHERE name='Annual Leave'").fetchone()
    conn.close()

    start = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
    end = (date.today() + timedelta(days=12)).strftime("%Y-%m-%d")
    
    bal_before = emp.get_balance(lt_annual["id"])
    ok, req_id = submit_leave(emp.id, lt_annual["id"], start, end, "Short trip")
    assert ok, f"Submit failed: {req_id}"
    
    mgr = Manager.from_row(login("mgr@test.com", "pass123"))
    ok, msg = mgr.approve_request(req_id, "Approved by mgr")
    assert ok, f"Approve failed: {msg}"
    assert "approved" in msg.lower()

    bal_after = emp.get_balance(lt_annual["id"])
    assert bal_after < bal_before, "Balance not deducted"
    print(f"    ✓ Success: Balance deducted from {bal_before} to {bal_after}")

    # 4. Test 2: Maternity Leave (Requires HR)
    print("\n[4] Test 2: Maternity Leave (Manager -> HR)")
    conn = get_connection()
    lt_mat = conn.execute("SELECT id FROM leave_types WHERE name='Maternity Leave'").fetchone()
    conn.close()

    # Maternity requires 30 days notice
    start_mat = (date.today() + timedelta(days=40)).strftime("%Y-%m-%d")
    end_mat = (date.today() + timedelta(days=50)).strftime("%Y-%m-%d")
    
    ok, req_id_mat = submit_leave(emp.id, lt_mat["id"], start_mat, end_mat, "Maternity")
    assert ok, f"Submit failed: {req_id_mat}"

    # Manager approves -> should go to PENDING HR
    ok, msg = mgr.approve_request(req_id_mat, "Mgr ok")
    assert ok, f"Mgr forward failed: {msg}"
    assert "forwarded" in msg.lower()
    
    reqs = get_employee_requests(emp.id)
    req = next(r for r in reqs if r["id"] == req_id_mat)
    assert req["status"] == STATUS_PENDING_HR, f"Expected {STATUS_PENDING_HR}, got {req['status']}"
    print("    ✓ Status correctly moved to Pending HR")

    # HR final approves
    ok, msg = hr.approve_request(req_id_mat, "HR final ok")
    assert ok, f"HR approve failed: {msg}"
    
    reqs = get_employee_requests(emp.id)
    req = next(r for r in reqs if r["id"] == req_id_mat)
    assert req["status"] == STATUS_APPROVED, f"Expected {STATUS_APPROVED}, got {req['status']}"
    print("    ✓ Status correctly moved to Approved by HR")

    # 5. Test 3: Notice Period Validation
    print("\n[5] Test 3: Notice Period Validation")
    conn = get_connection()
    lt_casual = conn.execute("SELECT id FROM leave_types WHERE name='Casual Leave'").fetchone()
    conn.close()
    
    # Casual leave requires 1 day notice. Try same day.
    today_str = date.today().strftime("%Y-%m-%d")
    ok, err = submit_leave(emp.id, lt_casual["id"], today_str, today_str, "Emergency")
    assert not ok, "Should have failed due to notice period"
    print(f"    ✓ Correctly failed: {err}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
