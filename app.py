import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# ── Bootstrap DB ──────────────────────────────────────────────────────────────
from db.database import init_db
init_db()

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LeaveFlow",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {background: #1E1B4B !important;}
[data-testid="stSidebar"] * {color: #E0E7FF !important;}
[data-testid="stSidebar"] .stButton button {
    background: #4F46E5 !important;
    color: white !important;
    border-radius: 8px;
    width: 100%;
}
.stTabs [data-baseweb="tab"] {font-weight: 600;}
.stMetric label {font-size: 0.78rem !important; color: #6B7280 !important;}
div[data-testid="metric-container"] {
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 0.8rem 1rem;
}
</style>
""", unsafe_allow_html=True)

from utils.notifications import get_unread, mark_all_read
from pages import login, employee_dashboard, manager_dashboard, hr_dashboard

# ── Session guard ─────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    login.show()
    st.stop()

user = st.session_state["user"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## 🌿 LeaveFlow")
    st.markdown(f"**{user['name']}**")
    st.caption(f"{user['role'].title()}  ·  {user['department']}")
    st.divider()

    # Notifications
    unread = get_unread(user["id"])
    if unread:
        st.markdown(f"### 🔔 Notifications ({len(unread)})")
        for n in unread:
            st.info(n["message"])
        if st.button("Mark all read"):
            mark_all_read(user["id"])
            st.rerun()
    else:
        st.caption("🔕 No new notifications")

    st.divider()
    if st.button("🚪 Sign Out"):
        del st.session_state["user"]
        st.rerun()

# ── Role routing ──────────────────────────────────────────────────────────────
role = user["role"]

if role == "employee":
    employee_dashboard.show(user)
elif role == "manager":
    # Managers also have employee dashboard
    view = st.radio("View as", ["Manager", "Employee"], horizontal=True, label_visibility="collapsed")
    if view == "Manager":
        manager_dashboard.show(user)
    else:
        employee_dashboard.show(user)
elif role == "hr":
    hr_dashboard.show(user)
else:
    st.error(f"Unknown role: {role}")
