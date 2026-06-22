import streamlit as st
import database as db

st.title("⚙️ Settings")

if st.session_state.user:
    profile = st.session_state.get("profile", {})
    st.subheader("Account Profile")
    st.write(f"**Email:** {st.session_state.user.email}")

    with st.container(border=True):
        with st.form("profile_form"):
            name = st.text_input("Name", value=profile.get("name", ""))
            position = st.text_input("Position", value=profile.get("position", ""))
            institution = st.text_input(
                "Institution", value=profile.get("institution", "")
            )

            if st.form_submit_button("Update Profile", width="stretch"):
                db.update_profile(st.session_state.user.id, name, position, institution)
                st.session_state.profile["name"] = name
                st.session_state.profile["position"] = position
                st.session_state.profile["institution"] = institution
                st.success("Profile updated!")
                st.rerun()

    st.divider()
    if st.button("Sign Out", type="primary", width="stretch"):
        db.sign_out()
        st.session_state.user = None
        if "profile" in st.session_state:
            del st.session_state.profile
        st.rerun()
else:
    st.info("You must be signed in to view your profile.")
