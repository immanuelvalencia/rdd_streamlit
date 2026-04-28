import streamlit as st
import database as db

st.title("🔐 Welcome to RDD")
st.markdown("Please sign in or create an account to access the Road Damage Detection dashboard.")

tab1, tab2 = st.tabs(["Sign In", "Create Account"])

with tab1:
    with st.form("signin_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In", type="primary", width="stretch"):
            if email and password:
                with st.spinner("Signing in..."):
                    try:
                        res = db.sign_in(email, password)
                        st.session_state.user = res.user
                        profile = db.get_profile(res.user.id)
                        if profile:
                            st.session_state.profile = profile
                        else:
                            st.session_state.profile = {"name": "Unknown", "position": "Unknown"}
                        st.success("Signed in successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sign in failed. Please check your credentials.")
            else:
                st.warning("Please enter both email and password.")

with tab2:
    with st.form("signup_form"):
        new_name = st.text_input("Name")
        new_position = st.text_input("Position")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password", help="Password must be at least 6 characters.")
        if st.form_submit_button("Create Account", type="primary", width="stretch"):
            if new_name and new_email and len(new_password) >= 6:
                with st.spinner("Creating account..."):
                    try:
                        res = db.sign_up(new_email, new_password, new_name, new_position)
                        st.success("Account created successfully! You can now sign in.")
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")
            else:
                st.warning("Please provide your name, a valid email, and a password of at least 6 characters.")
