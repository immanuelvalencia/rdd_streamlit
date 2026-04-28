import streamlit as st
import pandas as pd
import os
import database as db
import mock_ai

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if 'target_project' in st.session_state:
    st.query_params["id"] = st.session_state.target_project
    del st.session_state.target_project

proj_id = st.query_params.get("id")

if not proj_id:
    st.error("No project selected.")
    if st.button("← Back to Projects"):
        st.switch_page("pages/projects.py")
    st.stop()

if st.button("← Back to All Projects"):
    st.query_params.clear()
    st.switch_page("pages/projects.py")

projects_df = db.get_projects()

if projects_df.empty or proj_id not in projects_df['id'].astype(str).values:
    st.error("Project not found.")
    st.stop()

selected_proj_row = projects_df[projects_df['id'].astype(str) == str(proj_id)].iloc[0]
user_id = selected_proj_row.get('user_id')

name = selected_proj_row.get('name', 'Unnamed Project')
street = selected_proj_row.get('street', 'N/A')
city = selected_proj_row.get('city', 'N/A')
region = selected_proj_row.get('region', 'N/A')
lat = selected_proj_row.get('latitude')
lon = selected_proj_row.get('longitude')

creator = selected_proj_row.get('creator_name')
if pd.isna(creator) or creator is None:
    creator = selected_proj_row.get('creator_email', 'Unknown')

created_at = str(selected_proj_row.get('created_at', ''))
if 'T' in created_at:
    created_at = created_at.split('T')[0]

@st.dialog("Delete Project")
def delete_project_dialog(p_id, p_name):
    st.warning("Deleting this project will permanently remove all associated media and AI detections from Supabase.")
    confirm_name = st.text_input(f"Type '{p_name}' to confirm deletion:")
    if st.button("Delete Project", type="primary", disabled=(confirm_name != p_name)):
        db.delete_project(p_id)
        st.success("Project deleted.")
        st.query_params.clear()
        st.switch_page("pages/projects.py")

col_info, col_btn = st.columns([4, 1])

with col_info:
    st.markdown(f"## 📁 {name}")
    st.write(f"**Location:** {street}, {city}, {region}")
    if pd.notnull(lat) and pd.notnull(lon):
        st.write(f"**Coordinates:** {lat:.5f}, {lon:.5f}")
    st.write(f"**Created By:** {creator} on {created_at}")

with col_btn:
    st.write("") 
    st.write("")
    if st.session_state.user and st.session_state.user.id == user_id:
        if st.button("🗑️ Delete Project", type="primary", use_container_width=True):
            delete_project_dialog(proj_id, name)

st.divider()

tab1, tab2 = st.tabs(["Media Gallery & Detections", "Upload New Media"])

with tab1:
    st.subheader("Media Gallery")
    media_df = db.get_media_for_project(proj_id)
    
    if not media_df.empty:
        for _, row in media_df.iterrows():
            with st.expander(f"📄 {row['filename']}  |  Status: {row['status'].capitalize()}", expanded=(row['status']=='pending')):
                meta_col, det_col = st.columns([1, 2])
                with meta_col:
                    st.write(f"**Uploaded:** {row['uploaded_at']}")
                    if os.path.exists(row['file_path']) and row['file_path'].lower().endswith(('.png', '.jpg', '.jpeg')):
                        st.image(row['file_path'], width="stretch")
                
                with det_col:
                    if row['status'] == 'completed':
                        supabase = db.init_connection()
                        resp = supabase.table("detections").select("damage_type, confidence").eq("media_id", row['id']).execute()
                        detections_df = pd.DataFrame(resp.data)
                        
                        if not detections_df.empty:
                            st.write("**AI Detections:**")
                            st.dataframe(
                                detections_df, 
                                width="stretch",
                                hide_index=True,
                                column_config={
                                    "damage_type": "Damage Type",
                                    "confidence": st.column_config.ProgressColumn("Confidence", format="%.2f", min_value=0, max_value=1)
                                }
                            )
                        else:
                            st.info("No damages detected.")
                    else:
                        st.info("Pending AI processing...")
    else:
        st.info("No media uploaded for this project yet.")

with tab2:
    if not st.session_state.user:
        st.warning("You must be logged in to upload media.")
    else:
        st.subheader("Upload Media")
        with st.container(border=True):
            uploaded_file = st.file_uploader("Choose an image or video file", type=['jpg', 'jpeg', 'png', 'mp4'])
            if uploaded_file is not None:
                if st.button("Upload & Process", type="primary", width="stretch"):
                    with st.spinner('Uploading to Supabase and running AI detection...'):
                        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        media_id = db.add_media(proj_id, uploaded_file.name, file_path)
                        mock_ai.process_media(media_id)
                        st.success("File uploaded and processed!")
                        import time
                        time.sleep(1)
                        st.rerun()
