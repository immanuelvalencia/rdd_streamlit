import streamlit as st
import pandas as pd
import os
import database as db
import mock_ai
import folium
from streamlit_folium import st_folium

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@st.cache_data(ttl=3300)
def signed_image_url(file_path: str) -> str:
    """Returns a signed URL for display. Cached for 55 min to minimise API calls."""
    return db.create_signed_url(file_path)

# --- BUTTON STYLING ---
st.markdown("""
<style>
/* Primary buttons — vibrant indigo */
button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: opacity 0.2s ease, transform 0.1s ease !important;
}
button[kind="primary"]:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
button[kind="primary"]:active {
    transform: translateY(0px) !important;
}

/* Secondary / default buttons */
button[kind="secondary"] {
    background: transparent !important;
    border: 1.5px solid #4f46e5 !important;
    color: #4f46e5 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: background 0.2s ease, color 0.2s ease !important;
}
button[kind="secondary"]:hover {
    background: #4f46e5 !important;
    color: white !important;
}

/* Tertiary / borderless buttons (Open Project cards) */
button[kind="borderless"] {
    background: transparent !important;
    border: 1.5px solid #6b7280 !important;
    color: #6b7280 !important;
    border-radius: 8px !important;
    transition: border-color 0.2s, color 0.2s !important;
}
button[kind="borderless"]:hover {
    border-color: #4f46e5 !important;
    color: #4f46e5 !important;
}
</style>
""", unsafe_allow_html=True)

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("📂 Projects")

# --- MODAL: CREATE PROJECT ---
@st.dialog("Create New Project", width="large")
def create_project_dialog():
    st.write("Fill in the details below. Click on the map to set coordinates.")

    name = st.text_input("Project Name *")

    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("Region", ["NCR", "Region III", "Region IV-A", "Region VII", "Region XI"])
    with col2:
        cities = []
        if region == "NCR": cities = ["Manila", "Quezon City", "Makati", "Taguig"]
        elif region == "Region III": cities = ["San Fernando", "Angeles", "Olongapo"]
        elif region == "Region IV-A": cities = ["Antipolo", "Dasmarinas", "Santa Rosa"]
        elif region == "Region VII": cities = ["Cebu City", "Mandaue", "Lapu-Lapu"]
        elif region == "Region XI": cities = ["Davao City", "Tagum", "Digos"]
        city = st.selectbox("City", cities)

    street = st.text_input("Street Address")

    st.write("📍 **Pin Location on Map**")

    # Persist pinned location in session state (never rerun inside dialog — it closes it)
    if "dialog_pin" not in st.session_state:
        st.session_state.dialog_pin = None

    # On each render, prefer the freshest click from st_folium over stored state
    pin = st.session_state.dialog_pin
    center = [pin["lat"], pin["lon"]] if pin else [14.5995, 120.9842]
    m = folium.Map(location=center, zoom_start=13 if pin else 11)

    if pin:
        folium.Marker(
            location=[pin["lat"], pin["lon"]],
            tooltip=f"{pin['lat']:.5f}, {pin['lon']:.5f}",
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
        ).add_to(m)

    # returned_objects limits what triggers a rerun — only last_clicked matters
    map_data = st_folium(m, height=320, width="100%", returned_objects=["last_clicked"])

    # When clicked, rerun ONLY the dialog fragment (scope="fragment") so it stays open
    # and rebuilds the map with the new pin immediately — no double-click needed.
    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        new_pin = {"lat": clicked["lat"], "lon": clicked["lng"]}
        if new_pin != st.session_state.dialog_pin:
            st.session_state.dialog_pin = new_pin
            st.rerun(scope="fragment")  # reruns dialog only, does NOT close it

    lat, lon = 0.0, 0.0
    if pin:
        lat, lon = pin["lat"], pin["lon"]
        st.success(f"📍 Pinned: **{lat:.5f}**, **{lon:.5f}**")
    else:
        st.info("Click anywhere on the map to drop a pin.")

    if st.button("Save Project", type="primary", width="stretch"):
        if not name:
            st.error("Project Name is required.")
        else:
            db.add_project(name, region, city, street, lat, lon, st.session_state.user.id)
            st.session_state.dialog_pin = None  # clear for next time
            st.success(f"Project '{name}' created!")
            st.rerun()

with col_btn:
    if st.session_state.user:
        st.write("")  # vertical alignment
        st.write("")
        if st.button("➕ New Project", type="primary", width="stretch"):
            create_project_dialog()
    else:
        st.write("")
        st.write("")
        st.caption("Log in to create projects")

st.divider()

try:
    projects_df = db.get_projects()
except Exception as e:
    st.error(f"Failed to fetch projects from Supabase. Ensure your secrets are configured. Error: {e}")
    st.stop()

# --- GRID VIEW ---
if projects_df.empty:
    st.info("No projects found.")
else:
    st.markdown("### Project Directory")
    cols = st.columns(3)
    for index, row in projects_df.iterrows():
        col = cols[index % 3]
        with col:
            with st.container(border=True):
                media_df = db.get_media_for_project(row['id'])
                if not media_df.empty:
                    image_rows = media_df[
                        media_df['file_path'].str.lower()
                        .str.split('?').str[0]
                        .str.endswith(('.png', '.jpg', '.jpeg'), na=False)
                    ]
                    if not image_rows.empty:
                        thumb_url = signed_image_url(image_rows.iloc[0]['file_path'])
                        st.image(thumb_url, width="stretch")
                    else:
                        st.info("📁 Media Uploaded")
                else:
                    st.info("📁 Empty Project")

                st.markdown(f"#### {row.get('name', 'Unnamed Project')}")

                street = row.get('street', 'N/A')
                city = row.get('city', 'N/A')
                region = row.get('region', 'N/A')
                st.caption(f"📍 {street}, {city}, {region}")

                lat = row.get('latitude')
                lon = row.get('longitude')
                if pd.notnull(lat) and pd.notnull(lon):
                    st.caption(f"🧭 {lat:.4f}, {lon:.4f}")

                created_str = str(row['created_at'])
                if 'T' in created_str:
                    created_str = created_str.split('T')[0] + " " + created_str.split('T')[1][:5]
                st.caption(f"🕒 {created_str}")

                creator = row.get('creator_email', 'Unknown')
                st.caption(f"👤 Created by: {creator}")

                if st.button("Open Project →", key=f"open_{row['id']}", width="stretch"):
                    st.session_state.target_project = row['id']
                    st.switch_page("pages/project_details.py")
