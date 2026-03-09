import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.manager import Manager
from services.leave_service import get_pending_requests_for_manager, get_team_calendar
from config import STATUS_APPROVED


def show(user: dict):
    mgr = Manager.from_row(user)
    st.markdown(f"## 🗂 Manager Dashboard")
    st.caption(f"{user['name']}  ·  {user['department']}")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["⏳ Pending Requests", "✅ Approved Leave", "📅 Team Calendar"])

    # ── Tab 1: Pending ────────────────────────────────────────────────────────
    with tab1:
        pending = get_pending_requests_for_manager(mgr.id)
        if not pending:
            st.success("🎉 No pending requests. You're all caught up!")
        else:
            st.markdown(f"**{len(pending)} pending request(s)**")
            for r in pending:
                # Check conflicts
                conflicts = mgr.check_team_conflict(
                    r["start_date"], r["end_date"], exclude_employee_id=r["employee_id"]
                )

                with st.expander(
                    f"👤 {r['employee_name']} — {r['leave_type_name']}  |  "
                    f"{r['start_date']} → {r['end_date']}  |  {r['working_days']:.1f} days"
                ):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Employee",    r["employee_name"])
                    col2.metric("Department",  r["department"])
                    col3.metric("Working Days", f"{r['working_days']:.1f}")

                    col4, col5 = st.columns(2)
                    col4.metric("Leave Type", r["leave_type_name"])
                    col5.metric("Submitted",  r["submitted_at"][:10] if r["submitted_at"] else "—")

                    if r["reason"]:
                        st.caption(f"📝 Reason: {r['reason']}")
                    
                    if r.get("attachment_path"):
                        try:
                            with open(r["attachment_path"], "rb") as f:
                                st.download_button(
                                    "📎 View Attachment",
                                    f,
                                    file_name=os.path.basename(r["attachment_path"]),
                                    key=f"dl_mgr_{r['id']}"
                                )
                        except FileNotFoundError:
                            st.error("Attachment file not found.")

                    if conflicts:
                        names = ", ".join(c["name"] for c in conflicts)
                        st.warning(f"⚠️ Conflict: **{names}** also has approved leave in this period.")

                    st.markdown("---")
                    note = st.text_input(
                        "Note (required for rejection)",
                        key=f"note_{r['id']}",
                        placeholder="Add a note for the employee...",
                    )
                    col_a, col_b, _ = st.columns([1, 1, 2])
                    with col_a:
                        if st.button("✅ Approve", key=f"approve_{r['id']}", type="primary"):
                            ok, msg = mgr.approve_request(r["id"], note)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{r['id']}"):
                            ok, msg = mgr.reject_request(r["id"], note)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    # ── Tab 2: Approved ───────────────────────────────────────────────────────
    with tab2:
        approved = mgr.get_team_requests(status=STATUS_APPROVED)
        if not approved:
            st.info("No approved leave records yet.")
        else:
            for r in approved:
                with st.expander(f"👤 {r['employee_name']} — {r['leave_type_name']} | {r['start_date']} → {r['end_date']}"):
                    st.write(f"**Days:** {r['working_days']:.1f}")
                    if r['reason']: st.write(f"**Reason:** {r['reason']}")
                    if r['manager_note']: st.write(f"**Note:** {r['manager_note']}")
                    if r.get("attachment_path"):
                        try:
                            with open(r["attachment_path"], "rb") as f:
                                st.download_button(
                                    "📎 View Attachment",
                                    f,
                                    file_name=os.path.basename(r["attachment_path"]),
                                    key=f"dl_mgr_appr_{r['id']}"
                                )
                        except FileNotFoundError:
                            st.error("Attachment file not found.")

    # ── Tab 3: Team Calendar ──────────────────────────────────────────────────
    with tab3:
        st.markdown("### Team Leave — Next 30 Days")
        team = mgr.get_team_members()
        approved_leave = get_team_calendar(mgr.id)

        today = date.today()
        days  = [today + timedelta(days=i) for i in range(30)]

        # Build a dict: employee_id -> set of leave dates
        leave_map: dict[int, set] = {m["id"]: set() for m in team}
        for req in approved_leave:
            eid = req["employee_id"]
            if eid in leave_map:
                d = date.fromisoformat(req["start_date"])
                end = date.fromisoformat(req["end_date"])
                while d <= end:
                    leave_map[eid].add(d)
                    d += timedelta(days=1)

        if not team:
            st.info("No team members assigned yet.")
        else:
            # Header row
            header = ["Employee"] + [d.strftime("%d %b") for d in days]
            rows = []
            for m in team:
                row = [m["name"]]
                for d in days:
                    if d.weekday() >= 5:
                        row.append("·")
                    elif d in leave_map.get(m["id"], set()):
                        row.append("🌴")
                    else:
                        row.append("")
                rows.append(row)

            cal_df = pd.DataFrame(rows, columns=header)
            st.dataframe(
                cal_df.set_index("Employee"),
                use_container_width=True,
                height=min(400, 50 + len(team) * 35),
            )
            st.caption("🌴 = On leave  ·  · = Weekend")
