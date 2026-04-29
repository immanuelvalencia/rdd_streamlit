import streamlit as st
import pandas as pd
import os
import database as db
import mock_ai
from ai.yolov11_inference import is_model_available
from ai import processor as ai_processor
import time
import re
from collections import defaultdict

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@st.cache_data(ttl=3300)
def signed_image_url(file_path: str) -> str:
    """Returns a signed URL for display. Cached 55 min to minimise API calls."""
    return db.create_signed_url(file_path)

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

name     = selected_proj_row.get('name', 'Unnamed Project')
street   = selected_proj_row.get('street', 'N/A')
city     = selected_proj_row.get('city', 'N/A')
region   = selected_proj_row.get('region', 'N/A')
lat      = selected_proj_row.get('latitude')
lon      = selected_proj_row.get('longitude')

creator = selected_proj_row.get('creator_name')
if pd.isna(creator) or creator is None:
    creator = selected_proj_row.get('creator_email', 'Unknown')

created_at = str(selected_proj_row.get('created_at', ''))
if 'T' in created_at:
    created_at = created_at.split('T')[0]

# ── Dialogs ───────────────────────────────────────────────────────────────────

@st.dialog("Delete Project")
def delete_project_dialog(p_id, p_name):
    st.warning("Deleting this project will permanently remove all associated media and AI detections from Supabase.")
    confirm_name = st.text_input(f"Type '{p_name}' to confirm deletion:")
    if st.button("Delete Project", type="primary", disabled=(confirm_name != p_name)):
        db.delete_project(p_id)
        st.success("Project deleted.")
        st.query_params.clear()
        st.switch_page("pages/projects.py")

@st.dialog("Upload Media", width="large")
def upload_media_dialog(p_id):
    upload_type = st.radio("Media Type", ["Image", "Video"], horizontal=True)

    if upload_type == "Image":
        uploaded_files = st.file_uploader(
            "Choose image(s)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True
        )
        if uploaded_files:
            st.caption(f"{len(uploaded_files)} file(s) selected — {'batch upload' if len(uploaded_files) > 1 else 'single upload'}")
            if st.button("⬆️ Upload Images", type="primary", width="stretch"):
                with st.spinner("Uploading to Supabase Storage..."):
                    is_batch = len(uploaded_files) > 1
                    batch_ts = int(time.time())
                    sub_folder = f"batch_{batch_ts}" if is_batch else None
                    batch_prefix = f"[Batch {batch_ts}] " if is_batch else ""
                    for f in uploaded_files:
                        db.add_media(
                            project_id=p_id,
                            filename=batch_prefix + f.name,
                            file_bytes=f.getbuffer().tobytes(),
                            sub_folder=sub_folder,
                        )
                st.success(f"✅ {len(uploaded_files)} image(s) uploaded!")
                time.sleep(1)
                st.rerun()
    else:
        uploaded_file = st.file_uploader("Choose a video", type=['mp4', 'avi', 'mov'])
        if uploaded_file:
            if st.button("⬆️ Upload Video", type="primary", width="stretch"):
                with st.spinner("Uploading video to Supabase Storage..."):
                    db.add_media(
                        project_id=p_id,
                        filename=uploaded_file.name,
                        file_bytes=uploaded_file.getbuffer().tobytes(),
                    )
                st.success("✅ Video uploaded!")
                time.sleep(1)
                st.rerun()

# ── Project Header ────────────────────────────────────────────────────────────

col_info, col_actions = st.columns([4, 1])

with col_info:
    st.markdown(f"## 📁 {name}")
    st.write(f"**Location:** {street}, {city}, {region}")
    if pd.notnull(lat) and pd.notnull(lon):
        st.write(f"**Coordinates:** {lat:.5f}, {lon:.5f}")
    st.write(f"**Created By:** {creator} on {created_at}")

with col_actions:
    st.write("")
    st.write("")
    if st.session_state.user:
        if st.button("⬆️ Upload Media", type="primary", width="stretch"):
            upload_media_dialog(proj_id)
        if st.session_state.user.id == user_id:
            if st.button("🗑️ Delete Project", width="stretch"):
                delete_project_dialog(proj_id, name)

st.divider()

# ── Shared data fetched once, used across all tabs ────────────────────────────

media_df = db.get_media_for_project(proj_id)

def build_media_groups(df):
    groups = defaultdict(list)
    for _, row in df.iterrows():
        match = re.match(r'^(\[Batch .*?\])\s*(.*)', row['filename'])
        groups[match.group(1) if match else f"single_{row['id']}"].append(row)
    return groups

media_groups = build_media_groups(media_df) if not media_df.empty else {}

def get_project_detections(df):
    if df.empty:
        return pd.DataFrame()
    supabase = db.init_connection()
    media_ids = df['id'].tolist()
    resp = supabase.table("detections").select("media_id, damage_type, confidence").in_("media_id", media_ids).execute()
    det = pd.DataFrame(resp.data)
    if not det.empty:
        det = det.merge(df[['id', 'filename']], left_on='media_id', right_on='id', how='left').drop(columns='id')
    return det

det_df = get_project_detections(media_df)

tab_gallery, tab_run, tab_detections = st.tabs([
    "📷 Media Gallery",
    "▶️ Run AI Model",
    "🤖 AI Detections",
])

# ── TAB 1: MEDIA GALLERY ─────────────────────────────────────────────────────
with tab_gallery:
    if media_df.empty:
        st.info("No media yet — click **⬆️ Upload Media** above to add files.")
    else:
        show_detections = st.checkbox("🔍 Show AI Detections (Bounding Boxes)", value=True, help="Toggle between original images and AI-annotated images with boxes.")
        
        for group_key, rows in media_groups.items():
            if group_key.startswith("single_"):
                row = rows[0]
                fp = row.get('file_path', '')
                is_image = fp and any(fp.lower().split('?')[0].endswith(e) for e in ('.png', '.jpg', '.jpeg'))
                label = f"📄 {row['filename']}  |  {row['status'].capitalize()}"
                
                with st.expander(label, expanded=False):
                    st.caption(f"Uploaded: {row['uploaded_at']}")
                    if is_image:
                        display_path = fp
                        if show_detections and row['status'] == 'completed':
                            # Try to show annotated image
                            display_path = f"projects/{proj_id}/detections/{row['id']}/annotated.jpg"
                        
                        st.image(signed_image_url(display_path), width="stretch")
                    else:
                        st.info("🎬 Video file — preview not available.")
            else:
                statuses = {r['status'] for r in rows}
                overall = "pending" if "pending" in statuses else "completed"
                label = f"📂 {group_key} ({len(rows)} images)  |  {overall.capitalize()}"
                
                with st.expander(label, expanded=False):
                    cols = st.columns(3)
                    for idx, row in enumerate(rows):
                        with cols[idx % 3]:
                            clean = re.sub(r'^\[Batch .*?\]\s*', '', row['filename'])
                            st.caption(clean)
                            fp = row.get('file_path', '')
                            is_image = fp and any(fp.lower().split('?')[0].endswith(e) for e in ('.png', '.jpg', '.jpeg'))
                            if is_image:
                                display_path = fp
                                if show_detections and row['status'] == 'completed':
                                    display_path = f"projects/{proj_id}/detections/{row['id']}/annotated.jpg"
                                
                                st.image(signed_image_url(display_path), width="stretch")


# ── TAB 2: RUN AI MODEL ───────────────────────────────────────────────────────
with tab_run:
    st.subheader("Run AI Model")
    if not st.session_state.user:
        st.warning("You must be logged in to run AI models.")
    elif media_df.empty:
        st.info("Upload media first — click **⬆️ Upload Media** above.")
    else:
        model_available = is_model_available()
        model_options = ["YOLOv11 - Road Damage", "Mock (Demo only)"]
        model_choice = st.selectbox(
            "Select AI Model",
            model_options,
            help="YOLOv11 requires best.pt in models/yolov11/weights/"
        )
        if model_choice == "YOLOv11 - Road Damage" and not model_available:
            st.warning("⚠️ Model weights not found at `models/yolov11/weights/best.pt`. Will fall back to mock mode.")
        elif model_choice == "YOLOv11 - Road Damage":
            st.success("✅ YOLOv11 model ready.")

        pending_media = media_df[media_df['status'] == 'pending']

        if pending_media.empty:
            st.info("✅ All media has already been processed. Check the 🤖 AI Detections tab for results.")
        else:
            st.write("Select media to process:")
            media_options = {}
            batch_mapping = defaultdict(list)

            for _, row in pending_media.iterrows():
                match = re.match(r'^(\[Batch .*?\])\s*(.*)', row['filename'])
                if match:
                    batch_id = match.group(1)
                    batch_mapping[batch_id].append(row['id'])
                else:
                    key = f"single_{row['id']}"
                    batch_mapping[key].append(row['id'])
                    media_options[key] = row['filename']

            for batch_id, ids in batch_mapping.items():
                if not batch_id.startswith("single_"):
                    media_options[batch_id] = f"{batch_id} ({len(ids)} images)"

            selected_keys = st.multiselect(
                "Pending Media",
                options=list(media_options.keys()),
                format_func=lambda x: media_options[x],
                default=list(media_options.keys()),
            )

            if st.button("▶️ Run AI Model", type="primary", width="stretch"):
                if selected_keys:
                    selected_ids = []
                    for key in selected_keys:
                        selected_ids.extend(batch_mapping[key])

                    use_real_model = is_model_available() and model_choice == "YOLOv11 - Road Damage"

                    progress = st.progress(0, text="Starting...")
                    errors = []

                    for i, m_id in enumerate(selected_ids):
                        progress.progress((i) / len(selected_ids), text=f"Processing {i+1}/{len(selected_ids)}...")
                        media_row = media_df[media_df['id'] == m_id].iloc[0]

                        if use_real_model:
                            result = ai_processor.process_media(
                                media_id=m_id,
                                project_id=proj_id,
                                file_path=media_row['file_path'],
                            )
                            if not result['success']:
                                errors.append(f"{media_row['filename']}: {result['error']}")
                        else:
                            mock_ai.process_media(m_id)

                    progress.progress(1.0, text="Done!")

                    if errors:
                        st.warning(f"Completed with {len(errors)} error(s):")
                        for e in errors:
                            st.caption(f"⚠️ {e}")
                    else:
                        st.success(f"✅ {len(selected_ids)} file(s) processed! Check the 🤖 AI Detections tab.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please select at least one media file.")

# ── TAB 3: AI DETECTIONS ─────────────────────────────────────────────────────
with tab_detections:
    if det_df.empty:
        st.info("No AI detections yet. Upload media and run the AI model first.")
    else:
        st.subheader("Detections by Upload")

        for group_key, rows in media_groups.items():
            group_media_ids = [r['id'] for r in rows]
            group_det = det_df[det_df['media_id'].isin(group_media_ids)]
            if group_det.empty:
                continue

            label = (
                f"📄 {rows[0]['filename']}"
                if group_key.startswith("single_")
                else f"📂 {group_key} ({len(rows)} images)"
            )

            with st.expander(label, expanded=True):
                summary = (
                    group_det.groupby('damage_type')['confidence']
                    .agg(count='count', avg_confidence='mean')
                    .reset_index()
                    .sort_values('count', ascending=False)
                )
                summary['avg_confidence'] = summary['avg_confidence'].round(3)

                col_tbl, col_chart = st.columns([1, 1])
                with col_tbl:
                    st.dataframe(
                        summary,
                        hide_index=True,
                        width="stretch",
                        column_config={
                            "damage_type": "Damage Type",
                            "count": st.column_config.NumberColumn("Count"),
                            "avg_confidence": st.column_config.ProgressColumn(
                                "Avg Confidence", format="%.3f", min_value=0, max_value=1
                            ),
                        },
                    )
                with col_chart:
                    st.bar_chart(summary.set_index('damage_type')['count'])

        st.divider()

        st.subheader("📊 Project Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Media Files", len(media_df))
        m2.metric("Processed", len(media_df[media_df['status'] == 'completed']))
        m3.metric("Total Detections", len(det_df))

        st.markdown("**Damage Type Distribution — All Media**")
        proj_summary = (
            det_df.groupby('damage_type')['confidence']
            .agg(count='count', avg_confidence='mean')
            .reset_index()
            .sort_values('count', ascending=False)
        )
        proj_summary['avg_confidence'] = proj_summary['avg_confidence'].round(3)

        col_ps1, col_ps2 = st.columns([1, 1])
        with col_ps1:
            st.dataframe(
                proj_summary,
                hide_index=True,
                width="stretch",
                column_config={
                    "damage_type": "Damage Type",
                    "count": st.column_config.NumberColumn("Count"),
                    "avg_confidence": st.column_config.ProgressColumn(
                        "Avg Confidence", format="%.3f", min_value=0, max_value=1
                    ),
                },
            )
        with col_ps2:
            st.bar_chart(proj_summary.set_index('damage_type')['count'])
