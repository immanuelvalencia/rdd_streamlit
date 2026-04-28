import streamlit as st
import pandas as pd
import os
import database as db
import mock_ai
import folium
from streamlit_folium import st_folium
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    m = folium.Map(location=[14.5995, 120.9842], zoom_start=11)
    map_data = st_folium(m, height=300, width=700)
    
    lat, lon = 0.0, 0.0
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"Selected Coordinates: {lat:.5f}, {lon:.5f}")
    else:
        st.info("Click anywhere on the map to set coordinates.")
        
    if st.button("Save Project", type="primary", use_container_width=True):
        if not name:
            st.error("Project Name is required.")
        else:
            db.add_project(name, region, city, street, lat, lon, st.session_state.user.id)
            st.success(f"Project '{name}' created!")
            st.rerun()

with col_btn:
    if st.session_state.user:
        st.write("") # Vertical alignment spacing
        st.write("")
        if st.button("➕ Create New Project", type="primary", width="stretch"):
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

# --- GRID VIEW (Shows all folders/projects) ---
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
                    latest_media = media_df.iloc[0]['file_path']
                    if os.path.exists(latest_media) and latest_media.lower().endswith(('.png', '.jpg', '.jpeg')):
                        st.image(latest_media, width="stretch")
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
                
                if st.button("Open Project", key=f"open_{row['id']}", width="stretch"):
                    st.session_state.target_project = row['id']
                    st.switch_page("pages/project_details.py")
