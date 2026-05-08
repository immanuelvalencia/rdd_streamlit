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
                            st.session_state.profile = {"name": "Unknown", "position": "Unknown", "institution": "Unknown"}
                        st.success("Signed in successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sign in failed. Please check your credentials.")
            else:
                st.warning("Please enter both email and password.")

    st.divider()
    with st.expander("Forgot Password?"):
        st.markdown("Enter your email address to receive a password reset link.")
        with st.form("forgot_password_form"):
            reset_email = st.text_input("Email", key="reset_email")
            if st.form_submit_button("Send Reset Link", type="primary", width="stretch"):
                if reset_email:
                    with st.spinner("Sending reset link..."):
                        try:
                            db.reset_password(reset_email)
                            st.success("If an account exists with that email, a password reset link has been sent.")
                        except Exception as e:
                            st.error(f"Failed to send reset link: {e}")
                else:
                    st.warning("Please enter your email address.")

with tab2:
    with st.form("signup_form"):
        new_email = st.text_input("Email")
        new_name = st.text_input("Name")
        new_institution = st.text_input("Institution")
        new_position = st.text_input("Position")
        new_password = st.text_input("Password", type="password", help="Password must be at least 6 characters.")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        agreement = st.checkbox("I agree to the [Terms and Conditions](#)")
        
        if st.form_submit_button("Create Account", type="primary", width="stretch"):
            if not agreement:
                st.warning("You must agree to the Terms and Conditions.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif new_name and new_email and len(new_password) >= 6:
                with st.spinner("Creating account..."):
                    try:
                        res = db.sign_up(new_email, new_password, new_name, new_position, new_institution)
                        st.success("Registration successful! Please check your email inbox to activate your account.")
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")
            else:
                st.warning("Please provide your name, a valid email, and a password of at least 6 characters.")
