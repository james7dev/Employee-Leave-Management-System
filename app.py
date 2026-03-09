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
    border: none;
    transition: all 0.3s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: #6366F1 !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    font-size: 1rem;
}
.stMetric label {font-size: 0.85rem !important; color: #6B7280 !important; font-weight: 500;}
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #F3F4F6;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.main .block-container {
    padding-top: 2rem;
    max-width: 1200px;
}
h1, h2, h3 {
    color: #111827;
    font-weight: 700 !important;
}
.stAlert {
    border-radius: 10px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

from utils.notifications import get_unread, mark_all_read
from pages import login, employee_dashboard, manager_dashboard, hr_dashboard, profile

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
    
    if st.button("👤 Profile"):
        st.session_state["page"] = "profile"
        st.rerun()

    if st.button("🚪 Sign Out"):
        del st.session_state["user"]
        if "page" in st.session_state:
            del st.session_state["page"]
        st.rerun()

# ── Routing ───────────────────────────────────────────────────────────────────
if st.session_state.get("page") == "profile":
    if st.button("⬅️ Back to Dashboard"):
        del st.session_state["page"]
        st.rerun()
    profile.show(user)
    st.stop()

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
elif role == "hr" or role == "admin":
    hr_dashboard.show(user)
else:
    st.error(f"Unknown role: {role}")
