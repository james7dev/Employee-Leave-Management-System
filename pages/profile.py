import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.auth_service import change_password
from models.employee import Employee

def show(user: dict):
    st.markdown(f"## 👤 User Profile")
    st.divider()

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Information")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {user['role'].title()}")
        st.write(f"**Department:** {user['department']}")
        
        st.markdown("### Leave Summary")
        emp = Employee.from_row(user)
        balances = emp.get_balances()
        for b in balances:
            st.write(f"**{b['leave_type_name']}:** {b['used_days']:.1f} used / {b['total_days']:.1f} total")

    with col2:
        st.markdown("### Change Password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password"):
            if not new_pw:
                st.error("Password cannot be empty.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            else:
                change_password(user["id"], new_pw)
                st.success("✅ Password updated successfully!")
