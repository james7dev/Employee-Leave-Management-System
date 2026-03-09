import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.auth_service import register_user, get_managers
from config import DEPARTMENTS


def show():
    st.markdown("""
    <style>
    .register-wrap {
        max-width: 500px;
        margin: 40px auto 0 auto;
    }
    .brand-title {
        font-size: 2.6rem;
        font-weight: 800;
        color: #4F46E5;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    .brand-sub {
        color: #6B7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .register-card {
        background: #fff;
        border-radius: 16px;
        padding: 2.2rem 2.4rem;
        box-shadow: 0 4px 32px rgba(79,70,229,0.10);
        border: 1px solid #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="brand-title">🌿 LeaveFlow</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-sub">Create your account</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="register-card">', unsafe_allow_html=True)
            
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email address", placeholder="john@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            
            dept = st.selectbox("Department", DEPARTMENTS)
            
            managers = get_managers()
            mgr_opts = {f"{m['name']} ({m['department']})": m["id"] for m in managers}
            mgr_label = st.selectbox("Assign Manager", list(mgr_opts.keys()))
            mgr_id = mgr_opts[mgr_label]

            if st.button("Create Account", use_container_width=True, type="primary"):
                if not name or not email or not password:
                    st.error("Please fill in all required fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Default role to 'employee' for self-registration
                    ok, result = register_user(name, email, password, "employee", dept, mgr_id)
                    if ok:
                        st.success("Account created successfully! You can now sign in.")
                        if st.button("Go to Login"):
                            st.session_state["page"] = "login"
                            st.rerun()
                    else:
                        st.error(f"Error: {result}")

            if st.button("Back to Login", use_container_width=True):
                st.session_state["page"] = "login"
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
