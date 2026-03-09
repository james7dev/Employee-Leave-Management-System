import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.auth_service import login


def show():
    st.markdown("""
    <style>
    .login-wrap {
        max-width: 420px;
        margin: 60px auto 0 auto;
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
    .login-card {
        background: #fff;
        border-radius: 16px;
        padding: 2.2rem 2.4rem;
        box-shadow: 0 4px 32px rgba(79,70,229,0.10);
        border: 1px solid #E5E7EB;
    }
    .demo-box {
        background: #F0F0FF;
        border-radius: 10px;
        padding: 0.8rem 1.1rem;
        margin-top: 1.4rem;
        font-size: 0.83rem;
        color: #4338CA;
        border: 1px solid #C7D2FE;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="brand-title">🌿 LeaveFlow</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-sub">Employee Leave Management System</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("### Sign in to your account")

            email    = st.text_input("Email address", placeholder="you@company.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pw")

            if st.button("Sign In", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    user = login(email.strip(), password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Invalid credentials or account is inactive.")

            st.markdown("""
            <div class="demo-box">
            <b>Demo credentials</b><br>
            HR Admin: <code>hr@company.com</code> / <code>admin123</code>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
