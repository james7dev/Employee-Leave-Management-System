import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.leave_service import (
    get_leave_types, submit_leave, get_employee_requests, check_conflict,
    get_request_approvals, get_request_documents
)
from models.employee import Employee
from config import (
    STATUS_DRAFT, STATUS_PENDING_MANAGER, STATUS_PENDING_HR, 
    STATUS_APPROVED, STATUS_REJECTED, STATUS_CANCELLED, STATUS_MORE_INFO_REQUIRED
)


STATUS_EMOJI = {
    STATUS_DRAFT:               "📝 Draft",
    STATUS_PENDING_MANAGER:     "🟡 Pending Manager",
    STATUS_PENDING_HR:          "🔵 Pending HR",
    STATUS_APPROVED:            "🟢 Approved",
    STATUS_REJECTED:            "🔴 Rejected",
    STATUS_CANCELLED:           "⚫ Cancelled",
    STATUS_MORE_INFO_REQUIRED:  "🟠 Info Required",
}

STATUS_COLOR = {
    STATUS_DRAFT:               "#F3F4F6",
    STATUS_PENDING_MANAGER:     "#FEF3C7",
    STATUS_PENDING_HR:          "#DBEAFE",
    STATUS_APPROVED:            "#D1FAE5",
    STATUS_REJECTED:            "#FEE2E2",
    STATUS_CANCELLED:           "#F3F4F6",
    STATUS_MORE_INFO_REQUIRED:  "#FFEDD5",
}


def show(user: dict):
    emp = Employee.from_row(user)

    st.markdown(f"## 👋 Hello, {user['name'].split()[0]}!")
    st.caption(f"{user['department']}  ·  {user['role'].title()}  ·  Joined: {user.get('date_joined', '—')}")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "✉️ Submit Leave", "📋 My Requests"])

    # ── Tab 1: Balances ───────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Leave Balances")
        balances = emp.get_balances()
        if not balances:
            st.info("No leave balances configured. Contact HR.")
        else:
            cols = st.columns(min(len(balances), 3))
            for i, b in enumerate(balances):
                remaining = b["total_days"] - b["used_days"]
                pct = remaining / b["total_days"] if b["total_days"] > 0 else 0
                color = "#10B981" if pct > 0.5 else ("#F59E0B" if pct > 0.2 else "#EF4444")
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style="background:#fff;border-radius:12px;padding:1.1rem 1.3rem;
                                box-shadow:0 2px 12px rgba(0,0,0,0.07);border:1px solid #E5E7EB;
                                margin-bottom:1rem;">
                        <div style="font-size:0.78rem;color:#6B7280;font-weight:600;
                                    text-transform:uppercase;letter-spacing:0.05em;">
                            {b['leave_type_name']}
                        </div>
                        <div style="font-size:2rem;font-weight:800;color:{color};margin:0.3rem 0;">
                            {remaining:.1f}
                        </div>
                        <div style="font-size:0.82rem;color:#9CA3AF;">
                            of {b['total_days']:.0f} days · used {b['used_days']:.1f}
                        </div>
                        <div style="margin-top:0.6rem;background:#F3F4F6;border-radius:99px;height:6px;">
                            <div style="width:{pct*100:.0f}%;background:{color};
                                        height:6px;border-radius:99px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Recent requests
        st.markdown("### Recent Requests")
        requests = get_employee_requests(emp.id)
        if not requests:
            st.info("No leave requests yet.")
        else:
            for r in requests[:5]:
                status_label = STATUS_EMOJI.get(r["status"], r["status"])
                bg = STATUS_COLOR.get(r["status"], "#fff")
                st.markdown(f"""
                <div style="background:{bg};border-radius:10px;padding:0.8rem 1.1rem;
                            margin-bottom:0.5rem;border:1px solid #E5E7EB;">
                    <b>{r['leave_type_name']}</b> &nbsp;|&nbsp;
                    {r['start_date']} → {r['end_date']} &nbsp;|&nbsp;
                    {r['working_days']:.1f} days &nbsp;|&nbsp; {status_label}
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 2: Submit Leave ───────────────────────────────────────────────────
    with tab2:
        st.markdown("### Submit a Leave Request")
        leave_types = get_leave_types()
        lt_map = {lt["name"]: lt for lt in leave_types}

        col_a, col_b = st.columns(2)
        with col_a:
            lt_name    = st.selectbox("Leave Type", list(lt_map.keys()))
            start_date = st.date_input("Start Date", min_value=date.today())
        with col_b:
            is_half    = st.checkbox("Half Day")
            if is_half:
                end_date = start_date
                st.info(f"Half Day: End Date set to {end_date}")
            else:
                end_date = st.date_input("End Date", min_value=start_date)

        reason = st.text_area("Reason (optional)", placeholder="Brief description of your leave reason...")
        
        lt = lt_map[lt_name]
        attachment_path = None
        if lt.get("requires_document"):
            st.info(f"📎 **{lt_name}** requires a supporting document.")
            uploaded_file = st.file_uploader("Upload Supporting Document", type=["pdf", "jpg", "png"], key="doc_uploader")
            if uploaded_file:
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                safe_name = os.path.basename(uploaded_file.name)
                attachment_path = os.path.join("uploads", f"{user['id']}_{safe_name}")
                with open(attachment_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

        if st.button("Submit Request", type="primary"):
            if lt.get("requires_document") and not attachment_path:
                st.error("❌ Supporting document is required for this leave type.")
            else:
                start = start_date.strftime("%Y-%m-%d")
                end   = end_date.strftime("%Y-%m-%d")

                conflicts = check_conflict(emp.id, start, end)
                if conflicts:
                    names = ", ".join(c["name"] for c in conflicts)
                    st.warning(f"⚠️ Heads up: {names} also have approved leave in this period.")

                ok, result = submit_leave(emp.id, lt["id"], start, end, reason, is_half, attachment_path)
                if ok:
                    st.success(f"✅ Leave request submitted! (Request #{result})")
                    st.rerun()
                else:
                    st.error(f"❌ {result}")

    # ── Tab 3: My Requests ────────────────────────────────────────────────────
    with tab3:
        col_t, col_btn = st.columns([3, 1])
        col_t.markdown("### All My Leave Requests")
        
        requests = get_employee_requests(emp.id)
        
        if requests:
            df_export = pd.DataFrame(requests)
            csv = df_export.to_csv(index=False).encode('utf-8')
            col_btn.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"leave_history_{user['id']}.csv",
                mime='text/csv',
            )

        if not requests:
            st.info("No requests found.")
            return

        for r in requests:
            status_label = STATUS_EMOJI.get(r["status"], r["status"])
            bg = STATUS_COLOR.get(r["status"], "#fff")
            with st.expander(
                f"{r['leave_type_name']}  |  {r['start_date']} → {r['end_date']}  |  {status_label}"
            ):
                col1, col2, col3 = st.columns(3)
                col1.metric("Working Days", f"{r['working_days']:.1f}")
                col2.metric("Submitted", r["submitted_at"][:10] if r["submitted_at"] else "—")
                col3.metric("Status", r["status"])

                if r["reason"]:
                    st.caption(f"📝 Reason: {r['reason']}")
                
                # Documents
                docs = get_request_documents(r["id"])
                for d in docs:
                    try:
                        with open(d["file_path"], "rb") as f:
                            st.download_button(
                                f"📎 View {os.path.basename(d['file_path'])}",
                                f,
                                file_name=os.path.basename(d['file_path']),
                                key=f"dl_{r['id']}_{d['id']}"
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

                if r["status"] in (STATUS_PENDING_MANAGER, STATUS_PENDING_HR, STATUS_MORE_INFO_REQUIRED, STATUS_APPROVED):
                    cancel_label = "Cancel Request" if r["status"] != STATUS_APPROVED else "Cancel Approved Leave"
                    if st.button(cancel_label, key=f"cancel_{r['id']}"):
                        ok, msg = emp.cancel_request(r["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
