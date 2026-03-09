import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.hr_admin import HRAdmin
from services.auth_service import get_managers
from services.leave_service import get_leave_types
from services.report_service import (
    get_leave_by_department, get_leave_type_summary,
    get_absence_rate, get_monthly_trend
)
from db.database import get_connection
from config import DEPARTMENTS, ROLES, CURRENT_YEAR

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

    tab1, tab2, tab3, tab4 = st.tabs(
        ["👥 Users", "📋 Leave Types", "📊 Reports", "🗒 All Requests"]
    )

    # ── Tab 1: Users ──────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### All Users")
        users = hr.get_all_users()
        if users:
            df = pd.DataFrame(users)[
                ["id", "name", "email", "role", "department", "manager_name", "is_active"]
            ]
            df.columns = ["ID", "Name", "Email", "Role", "Department", "Manager", "Active"]
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
            mgr_opts  = {f"{m['name']} ({m['department']})": m["id"] for m in managers}
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
                    st.success(f"✅ User created (ID: {result})")
                    st.rerun()
                else:
                    st.error(f"❌ {result}")

        st.markdown("---")
        st.markdown("### Deactivate / Activate User")
        uid_input = st.number_input("User ID", min_value=1, step=1, key="uid_action")
        col_d, col_a = st.columns(2)
        with col_d:
            if st.button("Deactivate"):
                ok, msg = hr.deactivate_user(int(uid_input))
                st.success(msg) if ok else st.error(msg)
                st.rerun()
        with col_a:
            if st.button("Activate"):
                ok, msg = hr.activate_user(int(uid_input))
                st.success(msg) if ok else st.error(msg)
                st.rerun()

    # ── Tab 2: Leave Types ────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Leave Type Configuration")
        leave_types = get_leave_types()
        for lt in leave_types:
            with st.expander(f"📌 {lt['name']}"):
                c1, c2, c3 = st.columns(3)
                max_days    = c1.number_input("Max Days/Year", min_value=1, max_value=365,
                                               value=lt["max_days_per_year"], key=f"md_{lt['id']}")
                req_approval = c2.checkbox("Requires Approval",
                                           value=bool(lt["requires_approval"]), key=f"ra_{lt['id']}")
                req_docs     = c3.checkbox("Requires Docs",
                                           value=bool(lt["requires_docs"]), key=f"rd_{lt['id']}")
                if st.button("Save Changes", key=f"save_{lt['id']}"):
                    ok, msg = hr.update_leave_type(lt["id"], max_days, req_approval, req_docs)
                    st.success(msg) if ok else st.error(msg)

        st.markdown("---")
        st.markdown("### Reset Annual Balances")
        st.caption("Resets used_days to 0 and syncs total_days from current leave type config.")
        reset_year = st.number_input("Year", min_value=2020, max_value=2100,
                                      value=CURRENT_YEAR, key="reset_year")
        if st.button("🔄 Reset All Balances", type="primary"):
            ok, msg = hr.reset_balances(int(reset_year))
            st.success(msg) if ok else st.error(msg)

    # ── Tab 3: Reports ────────────────────────────────────────────────────────
    with tab3:
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

            csv = df_abs.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv,
                               f"absence_report_{report_year}.csv", "text/csv")

    # ── Tab 4: All Requests ───────────────────────────────────────────────────
    with tab4:
        st.markdown("### All Leave Requests")
        all_req = hr.get_all_requests()
        if not all_req:
            st.info("No requests found.")
            return

        df_all = pd.DataFrame(all_req)

        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        status_filter = col_f1.selectbox(
            "Status", ["All", "Pending", "Approved", "Rejected", "Cancelled"], key="rf_status"
        )
        dept_filter = col_f2.selectbox(
            "Department", ["All"] + sorted(df_all["department"].unique().tolist()), key="rf_dept"
        )
        if status_filter != "All":
            df_all = df_all[df_all["status"] == status_filter]
        if dept_filter != "All":
            df_all = df_all[df_all["department"] == dept_filter]

        show_cols = ["employee_name", "department", "leave_type_name",
                     "start_date", "end_date", "working_days", "status", "submitted_at"]
        display_df = df_all[show_cols].copy()
        display_df.columns = ["Employee", "Department", "Leave Type",
                               "Start", "End", "Days", "Status", "Submitted"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export as CSV", csv, "all_requests.csv", "text/csv")
