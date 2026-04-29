import streamlit as st
import database as db

db.init_db()
st.set_page_config(page_title="Road Damage Detection", page_icon="🛣️", layout="wide")

if 'user' not in st.session_state:
    user, profile = db.restore_session()
    st.session_state.user = user
    if user:
        st.session_state.profile = profile

login_page           = st.Page("pages/login.py",           title="Login / Sign Up", icon="🔐", default=True)
analytics_page       = st.Page("pages/analytics.py",       title="Dashboard",       icon="📊")
projects_page        = st.Page("pages/projects.py",        title="Projects",        icon="📂")
project_details_page = st.Page("pages/project_details.py", title="Project Viewer",  icon="🔍", url_path="project")
settings_page        = st.Page("pages/settings.py",        title="Settings",        icon="⚙️")
about_page           = st.Page("pages/about.py",           title="About RCMED",      icon="🏢")

if st.session_state.user:
    profile = st.session_state.get('profile', {})
    name = profile.get('name', st.session_state.user.email)

    all_pages = [analytics_page, projects_page, about_page, project_details_page, settings_page]
    pg = st.navigation(all_pages, position="hidden")

    # ── Sidebar: Navigation ───────────────────────────────────────────────────
    st.sidebar.markdown("### Navigation")
    st.sidebar.page_link(analytics_page)
    st.sidebar.page_link(projects_page)
    st.sidebar.page_link(about_page)
    st.sidebar.page_link(settings_page)

    # ── Sidebar: User info + logout ───────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👤 **{name}**")
    if st.sidebar.button("🚪 Logout", width="stretch"):
        db.sign_out()
        st.session_state.user = None
        st.session_state.pop('profile', None)
        st.rerun()

else:
    all_pages = [login_page]
    pg = st.navigation(all_pages, position="hidden")

pg.run()
