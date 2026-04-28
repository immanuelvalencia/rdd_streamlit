import streamlit as st
import database as db

db.init_db()
st.set_page_config(page_title="Road Damage Detection", page_icon="🛣️", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

login_page = st.Page("pages/login.py", title="Login / Sign Up", icon="🔐", default=True)
analytics_page = st.Page("pages/analytics.py", title="Analytics", icon="📊")
projects_page = st.Page("pages/projects.py", title="Projects", icon="📂")
project_details_page = st.Page("pages/project_details.py", title="Project Viewer", icon="🔍", url_path="project")
settings_page = st.Page("pages/settings.py", title="Settings", icon="⚙️")

if st.session_state.user:
    profile = st.session_state.get('profile', {})
    name = profile.get('name', st.session_state.user.email)
    st.sidebar.success(f"**👤 Signed in as:** {name}")

all_pages = [login_page, analytics_page, projects_page, project_details_page, settings_page]
pg = st.navigation(all_pages, position="hidden")

st.sidebar.markdown("---")
st.sidebar.markdown("### Core Application")
st.sidebar.page_link(analytics_page)
st.sidebar.page_link(projects_page)

st.sidebar.markdown("### Account")
if st.session_state.user is None:
    st.sidebar.page_link(login_page)
else:
    st.sidebar.page_link(settings_page)

pg.run()
