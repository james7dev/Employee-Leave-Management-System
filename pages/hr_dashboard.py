import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.hr_admin import HRAdmin
from services.auth_service import get_managers
from services.leave_service import get_leave_types, get_request_approvals, get_request_documents
from services.report_service import (
    get_leave_by_department, get_leave_type_summary,
    get_absence_rate, get_monthly_trend
)
from db.database import get_connection
from config import DEPARTMENTS, ROLES, CURRENT_YEAR, STATUS_PENDING_HR


try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def show(user: dict):
    hr = HRAdmin.from_row(user)
    st.markdown("## 🏢 HR Admin Dashboard")
    st.caption(f"{user['name']}  ·  Human Resources")
    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["👥 Users", "📋 Leave Types", "📅 Holidays", "📥 Pending HR Review", "📊 Reports", "🗒 All Requests"]
    )

    # ── Tab 1: Users ──────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### All Users")
        users = hr.get_all_users()
        if users:
            df = pd.DataFrame(users)[
                ["id", "name", "email", "role", "department", "manager_name", "is_active", "date_joined"]
            ]
            df.columns = ["ID", "Name", "Email", "Role", "Department", "Manager", "Active", "Joined"]
            df["Active"] = df["Active"].map({1: "✅", 0: "❌"})
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### ➕ Create New User")
        col1, col2 = st.columns(2)
        with col1:
            new_name  = st.text_input("Full Name", key="new_name")
            new_email = st.text_input("Email", key="new_email")
            new_pw    = st.text_input("Temporary Password", type="password", key="new_pw")
        with col2:
            new_role  = st.selectbox("Role", ROLES, key="new_role")
            new_dept  = st.selectbox("Department", DEPARTMENTS, key="new_dept")
            managers  = get_managers()
            # Use unique labels to avoid key collisions
            mgr_opts  = {f"{m['name']} ({m['department']}) [ID: {m['id']}]": m["id"] for m in managers}
            mgr_opts  = {"(None)": None, **mgr_opts}
            mgr_label = st.selectbox("Manager", list(mgr_opts.keys()), key="new_mgr")
            mgr_id    = mgr_opts[mgr_label]

        if st.button("Create User", type="primary"):
            if not all([new_name, new_email, new_pw]):
                st.error("Name, email, and password are required.")
            else:
                ok, result = hr.create_user(new_name, new_email, new_pw,
                                             new_role, new_dept, mgr_id)
                if ok:
                    st.toast(f"✅ User created: {new_name}")
                    st.success(f"✅ User created (ID: {result})")
                    st.rerun()
                else:
                    st.error(f"❌ {result}")

    # ── Tab 2: Leave Types ────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Leave Type Configuration")
        leave_types = get_leave_types()
        for lt in leave_types:
            with st.expander(f"📌 {lt['name']}"):
                c1, c2, c3 = st.columns(3)
                quota    = c1.number_input("Annual Quota", min_value=0, max_value=365,
                                               value=lt["annual_quota"], key=f"md_{lt['id']}")
                req_hr       = c2.checkbox("Requires HR Approval",
                                           value=bool(lt["requires_hr"]), key=f"rh_{lt['id']}")
                req_docs     = c3.checkbox("Requires Docs",
                                           value=bool(lt["requires_document"]), key=f"rd_{lt['id']}")
                
                c4, c5 = st.columns(2)
                max_days = c4.number_input("Max Consecutive Days", min_value=0, value=lt["max_consecutive_days"] or 0, key=f"max_{lt['id']}")
                notice = c5.number_input("Notice Period (days)", min_value=0, value=lt["notice_period_days"], key=f"notice_{lt['id']}")

                if st.button("Save Changes", key=f"save_{lt['id']}"):
                    ok, msg = hr.update_leave_type(lt["id"], quota, req_hr, req_docs, max_days, notice)
                    st.success(msg) if ok else st.error(msg)

        st.markdown("---")
        st.markdown("### Reset Annual Balances")
        st.caption("Resets used_days to 0 and syncs total_days from current leave type config.")
        reset_year = st.number_input("Year", min_value=2020, max_value=2100,
                                      value=CURRENT_YEAR, key="reset_year")
        if st.button("🔄 Reset All Balances", type="primary"):
            ok, msg = hr.reset_balances(int(reset_year))
            st.success(msg) if ok else st.error(msg)

    # ── Tab 3: Holidays ───────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Public Holidays")
        holidays = hr.get_holidays()
        if holidays:
            df_hol = pd.DataFrame(holidays)[["id", "date", "name"]]
            df_hol.columns = ["ID", "Date", "Holiday Name"]
            st.dataframe(df_hol, use_container_width=True, hide_index=True)
        else:
            st.info("No public holidays defined.")

        st.markdown("---")
        st.markdown("### ➕ Add Holiday")
        h_date = st.date_input("Holiday Date")
        h_name = st.text_input("Holiday Name")
        if st.button("Add Holiday"):
            if not h_name:
                st.error("Holiday name is required.")
            else:
                ok, msg = hr.add_holiday(h_date.strftime("%Y-%m-%d"), h_name)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ── Tab 4: Pending HR Review ──────────────────────────────────────────────
    with tab4:
        st.markdown("### Requests Pending HR Final Approval")
        hr_pending = hr.get_hr_pending_requests()
        if not hr_pending:
            st.success("🎉 No requests pending HR review.")
        else:
            for r in hr_pending:
                with st.expander(f"👤 {r['employee_name']} — {r['leave_type_name']} | {r['start_date']} → {r['end_date']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Employee", r["employee_name"])
                    col2.metric("Department", r["department"])
                    col3.metric("Working Days", f"{r['working_days']:.1f}")
                    
                    if r["reason"]:
                        st.write(f"**Reason:** {r['reason']}")
                    
                    # Documents
                    docs = get_request_documents(r["id"])
                    for d in docs:
                        try:
                            with open(d["file_path"], "rb") as f:
                                st.download_button(
                                    f"📎 View {os.path.basename(d['file_path'])}",
                                    f,
                                    file_name=os.path.basename(d['file_path']),
                                    key=f"dl_hr_pend_{r['id']}_{d['id']}"
                                )
                        except FileNotFoundError:
                            st.error(f"File not found: {d['file_path']}")

                    # History / Approvals
                    approvals = get_request_approvals(r["id"])
                    if approvals:
                        st.markdown("---")
                        st.markdown("**Approval History:**")
                        for a in approvals:
                            action_label = a["action"].replace("_", " ")
                            st.write(f"**{a['timestamp'][:16]}** — {a['role'].title()} ({a['approver_name']}): {action_label}")
                            if a["comment"]:
                                st.info(f"💬 {a['comment']}")

                    st.markdown("---")
                    hr_note = st.text_input("HR Comment", key=f"hr_note_{r['id']}")
                    c_a, c_b = st.columns(2)
                    with c_a:
                        if st.button("✅ Final Approve", key=f"hr_appr_{r['id']}", type="primary"):
                            ok, msg = hr.approve_request(r["id"], hr_note)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with c_b:
                        if st.button("❌ Final Reject", key=f"hr_rej_{r['id']}"):
                            ok, msg = hr.reject_request(r["id"], hr_note)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)


    # ── Tab 5: Reports ────────────────────────────────────────────────────────
    with tab5:
        st.markdown("### Company Leave Reports")
        report_year = st.selectbox("Year", list(range(CURRENT_YEAR, CURRENT_YEAR - 5, -1)), key="rep_year")

        col_l, col_r = st.columns(2)

        # Bar chart: leave by department
        with col_l:
            st.markdown("#### Leave Days by Department")
            dept_data = get_leave_by_department(report_year)
            if dept_data and HAS_PLOTLY:
                df_dept = pd.DataFrame(dept_data)
                fig = px.bar(df_dept, x="department", y="total_days",
                             color="leave_type", barmode="stack",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(margin=dict(t=20, b=0), height=320,
                                  legend=dict(orientation="h", y=-0.3))
                st.plotly_chart(fig, use_container_width=True)
            elif dept_data:
                st.dataframe(pd.DataFrame(dept_data), use_container_width=True)
            else:
                st.info("No approved leave data for this year.")

        # Pie chart: leave type breakdown
        with col_r:
            st.markdown("#### Leave Type Breakdown")
            lt_data = get_leave_type_summary(report_year)
            if lt_data and HAS_PLOTLY:
                df_lt = pd.DataFrame(lt_data)
                fig2 = px.pie(df_lt, values="total_days", names="leave_type",
                              color_discrete_sequence=px.colors.qualitative.Set3)
                fig2.update_layout(margin=dict(t=20, b=0), height=320)
                st.plotly_chart(fig2, use_container_width=True)
            elif lt_data:
                st.dataframe(pd.DataFrame(lt_data), use_container_width=True)
            else:
                st.info("No data available.")

        # Monthly trend
        st.markdown("#### Monthly Trend")
        trend = get_monthly_trend(report_year)
        if trend and HAS_PLOTLY:
            df_trend = pd.DataFrame(trend)
            fig3 = px.line(df_trend, x="month", y="total_days", markers=True,
                           color_discrete_sequence=["#4F46E5"])
            fig3.update_layout(margin=dict(t=10, b=0), height=260)
            st.plotly_chart(fig3, use_container_width=True)

        # Absence rate table
        st.markdown("#### Employee Absence Rate")
        absence = get_absence_rate(report_year)
        if absence:
            df_abs = pd.DataFrame(absence)[["name", "department", "used_days", "absence_rate"]]
            df_abs.columns = ["Employee", "Department", "Days Used", "Absence Rate (%)"]
            st.dataframe(df_abs, use_container_width=True, hide_index=True)

    # ── Tab 6: All Requests ───────────────────────────────────────────────────
    with tab6:
        st.markdown("### All Leave Requests")
        all_req = hr.get_all_requests()
        if not all_req:
            st.info("No requests found.")
        else:
            df_all = pd.DataFrame(all_req)

            # Filters
            col_f1, col_f2, col_f3 = st.columns(3)
            status_filter = col_f1.selectbox(
                "Status", ["All", "Pending Manager", "Pending HR", "Approved", "Rejected", "Cancelled", "More Info Required"], key="rf_status"
            )
            dept_filter = col_f2.selectbox(
                "Department", ["All"] + sorted(df_all["department"].unique().tolist()), key="rf_dept"
            )
            if status_filter != "All":
                df_all = df_all[df_all["status"] == status_filter]
            if dept_filter != "All":
                df_all = df_all[df_all["department"] == dept_filter]

            for idx, r in df_all.iterrows():
                with st.expander(f"{r['employee_name']} | {r['leave_type_name']} | {r['start_date']} → {r['end_date']} | {r['status']}"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Employee:** {r['employee_name']}")
                    col1.write(f"**Department:** {r['department']}")
                    col1.write(f"**Days:** {r['working_days']:.1f}")
                    col2.write(f"**Submitted:** {r['submitted_at']}")
                    col2.write(f"**Status:** {r['status']}")
                    if r['reason']: st.write(f"**Reason:** {r['reason']}")
                    
                    approvals = get_request_approvals(r["id"])
                    for a in approvals:
                        st.write(f"**{a['role'].title()} ({a['approver_name']}):** {a['action']}")
                        if a["comment"]: st.info(f"💬 {a['comment']}")
