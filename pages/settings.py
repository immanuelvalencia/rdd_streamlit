import streamlit as st
import database as db

st.title("⚙️ Settings")

tab_profile, tab_prefs, tab_about = st.tabs(["Profile", "App Preferences", "About"])

with tab_profile:
    st.subheader("Account Profile")
    if st.session_state.user:
        profile = st.session_state.get('profile', {})
        st.write(f"**Email:** {st.session_state.user.email}")
        with st.form("profile_form"):
            name = st.text_input("Name", value=profile.get('name', ''))
            position = st.text_input("Position", value=profile.get('position', ''))
            if st.form_submit_button("Update Profile"):
                db.update_profile(st.session_state.user.id, name, position)
                st.session_state.profile['name'] = name
                st.session_state.profile['position'] = position
                st.success("Profile updated!")
                st.rerun()
                
        st.divider()
        if st.button("Sign Out", type="primary"):
            db.sign_out()
            st.session_state.user = None
            if 'profile' in st.session_state:
                del st.session_state.profile
            st.rerun()
    else:
        st.info("You must be signed in to view your profile.")

with tab_prefs:
    st.subheader("App Preferences")
    st.markdown("Customize your Road Damage Detection experience.")
    with st.container(border=True):
        st.toggle("Enable Dark Mode Theme (Requires App Restart)", value=False)
        st.slider("AI Detection Sensitivity", min_value=0.1, max_value=0.99, value=0.5, step=0.05, help="Adjust the minimum confidence threshold for AI detections.")
        st.selectbox("Default Export Format", ["CSV", "Excel", "JSON"])
        if st.button("Save Preferences"):
            st.success("Preferences saved successfully!")

with tab_about:
    st.subheader("About")
    st.markdown("""
    This Road Damage Detection (RDD) application is designed to automate the process of identifying and cataloging road anomalies such as potholes and cracks using AI inference. By integrating with Supabase, it provides a robust, persistent storage solution for all media and detection data.
    """)
    st.divider()
    st.subheader("Meet the Developer")
    with st.container(border=True):
        col1, col2 = st.columns([1, 3], gap="large")
        with col1:
            try:
                st.image("assets/profile.png", width="stretch")
            except Exception:
                st.info("Profile picture unavailable.")
        with col2:
            st.markdown("### Engr. Christopher F. Cunanan")
            st.markdown("""
            Christopher is a dedicated software engineer and systems architect with a passion for integrating modern AI solutions into practical, real-world infrastructure problems. 
            
            With a strong background in both civil engineering concepts and advanced computer vision applications, he spearheaded the development of this Road Damage Detection platform to streamline road maintenance surveys.
            
            *Contact: christopher.cunanan@example.com*
            """)
