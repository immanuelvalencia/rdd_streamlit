import streamlit as st
import pandas as pd
import os
import io
import zipfile
import requests as _requests
import database as db

from ai.yolov11_inference import is_model_available as yolov11_available
from ai.yolov8seg_inference import is_model_available as yolov8seg_available
from ai import processor as ai_processor
import time
import re
from collections import defaultdict

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@st.cache_data(ttl=3300)
def signed_image_url(file_path: str, cache_bust: int = 0) -> str:
    """Returns a signed URL for display. Cached 55 min to minimise API calls.
    The cache_bust parameter can be used to force a fresh URL from the browser's perspective.
    """
    url = db.create_signed_url(file_path)
    return f"{url}&t={cache_bust}" if "?" in url else f"{url}?t={cache_bust}"


if "target_project" in st.session_state:
    st.query_params["id"] = st.session_state.target_project
    del st.session_state.target_project

if "img_cache_bust" not in st.session_state:
    st.session_state.img_cache_bust = int(time.time())

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

if projects_df.empty or proj_id not in projects_df["id"].astype(str).values:
    st.error("Project not found.")
    st.stop()

selected_proj_row = projects_df[projects_df["id"].astype(str) == str(proj_id)].iloc[0]
user_id = selected_proj_row.get("user_id")

name = selected_proj_row.get("name", "Unnamed Project")
street = selected_proj_row.get("street", "N/A")
city = selected_proj_row.get("city", "N/A")
province = selected_proj_row.get("province", "N/A")
region = selected_proj_row.get("region", "N/A")
lat = selected_proj_row.get("latitude")
lon = selected_proj_row.get("longitude")

creator = selected_proj_row.get("creator_name")
if pd.isna(creator) or creator is None:
    creator = selected_proj_row.get("creator_email", "Unknown")

created_at = str(selected_proj_row.get("created_at", ""))
if "T" in created_at:
    created_at = created_at.split("T")[0]

# ── Dialogs ───────────────────────────────────────────────────────────────────


@st.dialog("Delete Project")
def delete_project_dialog(p_id, p_name):
    st.warning(
        "Deleting this project will permanently remove all associated media and AI detections from Supabase."
    )
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
            "Choose image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True
        )
        if uploaded_files:
            st.caption(
                f"{len(uploaded_files)} file(s) selected — {'batch upload' if len(uploaded_files) > 1 else 'single upload'}"
            )
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

        @st.cache_data
        def get_video_metadata(video_bytes):
            import cv2
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_bytes)
                tmp_path = tmp.name
            cap = cv2.VideoCapture(tmp_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            os.remove(tmp_path)
            return fps, total_frames

        uploaded_file = st.file_uploader("Choose a video", type=["mp4", "avi", "mov"])
        if uploaded_file:
            video_bytes = uploaded_file.getbuffer().tobytes()
            orig_fps, orig_total_frames = get_video_metadata(video_bytes)
            if not orig_fps:
                orig_fps = 30.0

            st.markdown(
                f"**Video Info:** {orig_fps:.1f} FPS | {orig_total_frames} total frames"
            )

            target_fps = st.slider(
                "Extraction Rate (Frames Per Second)",
                min_value=0.5,
                max_value=float(orig_fps),
                value=1.0,
                step=0.5,
                help="Higher FPS means more images to process.",
            )

            duration = orig_total_frames / orig_fps if orig_fps > 0 else 0
            expected_frames = int(duration * target_fps)

            st.info(
                f"📸 Approximately **{expected_frames} frames** will be extracted and uploaded."
            )

            if st.button("⬆️ Extract & Upload Frames", type="primary", width="stretch"):
                with st.spinner("Extracting frames and uploading to Supabase..."):
                    import cv2
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".mp4"
                    ) as tmp:
                        tmp.write(video_bytes)
                        tmp_path = tmp.name

                    cap = cv2.VideoCapture(tmp_path)
                    frame_interval = max(int(orig_fps / target_fps), 1)

                    frames = []
                    count = 0
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        if count % frame_interval == 0:
                            ret, buf = cv2.imencode(".jpg", frame)
                            if ret:
                                frames.append(buf.tobytes())
                        count += 1
                    cap.release()
                    try:
                        os.remove(tmp_path)
                    except:
                        pass

                    if frames:
                        batch_ts = int(time.time())
                        sub_folder = f"vid_batch_{batch_ts}"
                        batch_prefix = f"[Batch {batch_ts}] frame_"

                        for i, frame_bytes in enumerate(frames):
                            db.add_media(
                                project_id=p_id,
                                filename=f"{batch_prefix}{i+1}.jpg",
                                file_bytes=frame_bytes,
                                sub_folder=sub_folder,
                            )
                        st.success(f"✅ Extracted and uploaded {len(frames)} frames!")
                    else:
                        st.error("Could not extract any frames from the video.")

                time.sleep(1)
                st.rerun()


# ── Project Header ────────────────────────────────────────────────────────────

col_info, col_actions = st.columns([4, 1])

with col_info:
    st.markdown(f"## 📁 {name}")
    loc_parts = [street, city, province, region]
    loc_str = ", ".join([str(p).strip() for p in loc_parts if pd.notnull(p) and str(p).strip() and str(p).strip() != "N/A"])
    st.write(f"**Location:** {loc_str or 'N/A'}")
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
        match = re.match(r"^(\[Batch .*?\])\s*(.*)", row["filename"])
        groups[match.group(1) if match else f"single_{row['id']}"].append(row)
    return groups


media_groups = build_media_groups(media_df) if not media_df.empty else {}


def get_project_detections(df):
    if df.empty:
        return pd.DataFrame()
    supabase = db.init_connection()
    media_ids = df["id"].tolist()
    resp = (
        supabase.table("detections")
        .select("media_id, damage_type, confidence")
        .in_("media_id", media_ids)
        .execute()
    )
    det = pd.DataFrame(resp.data)
    if not det.empty:
        det = det.merge(
            df[["id", "filename"]], left_on="media_id", right_on="id", how="left"
        ).drop(columns="id")
    return det


det_df = get_project_detections(media_df)

tab_gallery, tab_run, tab_detections = st.tabs(
    [
        "📷 Media Gallery",
        "▶️ Run AI Model",
        "🤖 AI Detections",
    ]
)

# ── TAB 1: MEDIA GALLERY ─────────────────────────────────────────────────────
with tab_gallery:
    if media_df.empty:
        st.info("No media yet — click **⬆️ Upload Media** above to add files.")
    else:
        # Build a map of all completed image rows keyed by media ID
        completed_img_rows = {
            r["id"]: r
            for rows in media_groups.values()
            for r in rows
            if r["status"] == "completed"
            and r.get("file_path", "")
            and any(
                r["file_path"].lower().split("?")[0].endswith(e)
                for e in (".png", ".jpg", ".jpeg")
            )
        }
        all_completed_ids = list(completed_img_rows.keys())

        # Initialise selection set in session state
        if "gallery_selected" not in st.session_state:
            st.session_state.gallery_selected = set()

        # Helper: pre-seed checkbox keys so value= takes effect on rerun
        def _seed_checkboxes(ids, checked: bool):
            for mid in ids:
                st.session_state[f"gal_chk_{mid}"] = checked
            st.session_state.gallery_selected = (
                st.session_state.gallery_selected | set(ids)
                if checked
                else st.session_state.gallery_selected - set(ids)
            )

        # ── Toolbar: show-detections toggle ───────────────────────────────────
        show_detections = st.checkbox(
            "🔍 Show AI Detections",
            value=True,
            help="Toggle between original and AI-annotated images.",
        )

        # ── Gallery items ──────────────────────────────────────────────────────
        for group_key, rows in media_groups.items():
            if group_key.startswith("single_"):
                row = rows[0]
                fp = row.get("file_path", "")
                is_image = fp and any(
                    fp.lower().split("?")[0].endswith(e)
                    for e in (".png", ".jpg", ".jpeg")
                )
                label = f"📄 {row['filename']}  |  {row['status'].capitalize()}"

                with st.expander(label, expanded=False):
                    col_chk, col_cap, col_del = st.columns([1, 4, 1])
                    with col_chk:
                        if row["status"] == "completed" and is_image:
                            chk = st.checkbox(
                                "",
                                value=row["id"] in st.session_state.gallery_selected,
                                key=f"gal_chk_{row['id']}",
                                label_visibility="collapsed",
                            )
                            if chk:
                                st.session_state.gallery_selected.add(row["id"])
                            else:
                                st.session_state.gallery_selected.discard(row["id"])
                    with col_cap:
                        st.caption(f"Uploaded: {row['uploaded_at']}")
                    with col_del:
                        if (
                            st.session_state.user
                            and st.session_state.user.id == user_id
                        ):
                            if st.button("🗑️ Delete", key=f"del_single_{row['id']}"):
                                st.session_state.gallery_selected.discard(row["id"])
                                db.delete_media_batch([row["id"]])
                                st.rerun()

                    if is_image:
                        display_path = fp
                        if show_detections and row["status"] == "completed":
                            if (
                                pd.notna(row.get("storage_path"))
                                and row["storage_path"]
                            ):
                                display_path = row["storage_path"]
                            else:
                                display_path = f"projects/{proj_id}/detections/{row['id']}/annotated.jpg"
                        st.image(
                            signed_image_url(
                                display_path, cache_bust=st.session_state.img_cache_bust
                            ),
                            width="stretch",
                        )
                    else:
                        st.info("🎬 Video file — preview not available.")
            else:
                statuses = {r["status"] for r in rows}
                overall = "pending" if "pending" in statuses else "completed"

                # Completed images in this batch
                batch_completed = [
                    r
                    for r in rows
                    if r["status"] == "completed"
                    and r.get("file_path", "")
                    and any(
                        r["file_path"].lower().split("?")[0].endswith(e)
                        for e in (".png", ".jpg", ".jpeg")
                    )
                ]
                batch_completed_ids = [r["id"] for r in batch_completed]
                batch_all_sel = bool(batch_completed_ids) and all(
                    mid in st.session_state.gallery_selected
                    for mid in batch_completed_ids
                )

                label = (
                    f"📂 {group_key} ({len(rows)} images)  |  {overall.capitalize()}"
                )

                with st.expander(label, expanded=False):
                    hdr_left, hdr_mid, hdr_right = st.columns([3, 2, 2])
                    with hdr_left:
                        if (
                            st.session_state.user
                            and st.session_state.user.id == user_id
                        ):
                            if st.button(
                                "🗑️ Delete Entire Batch", key=f"del_batch_{group_key}"
                            ):
                                with st.spinner("Deleting batch from Supabase..."):
                                    batch_ids = [r["id"] for r in rows]
                                    st.session_state.gallery_selected -= set(batch_ids)
                                    db.delete_media_batch(batch_ids)
                                st.rerun()
                    with hdr_right:
                        if batch_completed_ids:

                            def _on_batch_select(
                                ids=batch_completed_ids,
                                key=f"gal_batch_sel_{group_key}",
                            ):
                                _seed_checkboxes(ids, st.session_state[key])

                            st.checkbox(
                                "Select All",
                                value=batch_all_sel,
                                key=f"gal_batch_sel_{group_key}",
                                on_change=_on_batch_select,
                            )

                    cols = st.columns(3)
                    for idx, row in enumerate(rows):
                        with cols[idx % 3]:
                            fp = row.get("file_path", "")
                            is_image = fp and any(
                                fp.lower().split("?")[0].endswith(e)
                                for e in (".png", ".jpg", ".jpeg")
                            )
                            clean = re.sub(r"^\[Batch .*?\]\s*", "", row["filename"])

                            if row["status"] == "completed" and is_image:
                                chk = st.checkbox(
                                    clean,
                                    value=row["id"]
                                    in st.session_state.gallery_selected,
                                    key=f"gal_chk_{row['id']}",
                                )
                                if chk:
                                    st.session_state.gallery_selected.add(row["id"])
                                else:
                                    st.session_state.gallery_selected.discard(row["id"])
                            else:
                                st.caption(clean)

                            if is_image:
                                display_path = fp
                                if show_detections and row["status"] == "completed":
                                    if (
                                        pd.notna(row.get("storage_path"))
                                        and row["storage_path"]
                                    ):
                                        display_path = row["storage_path"]
                                    else:
                                        display_path = f"projects/{proj_id}/detections/{row['id']}/annotated.jpg"
                                st.image(
                                    signed_image_url(
                                        display_path,
                                        cache_bust=st.session_state.img_cache_bust,
                                    ),
                                    width="stretch",
                                )

        # ── Download bar ───────────────────────────────────────────────────────
        selected_in_proj = [
            mid for mid in st.session_state.gallery_selected if mid in all_completed_ids
        ]
        if selected_in_proj:
            st.divider()
            dl_count = len(selected_in_proj)
            bar_left, bar_right = st.columns([3, 1])
            with bar_left:
                st.markdown(f"📸 **{dl_count}** annotated image(s) selected")
            with bar_right:
                if st.button(
                    "📦 Prepare & Download ZIP",
                    type="primary",
                    width="stretch",
                    key="gal_dl_zip",
                ):
                    id_to_name = {
                        r["id"]: re.sub(r"^\[Batch .*?\]\s*", "", r["filename"])
                        for _, r in media_df.iterrows()
                    }
                    zip_buf = io.BytesIO()
                    errors_dl = []
                    with zipfile.ZipFile(
                        zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED
                    ) as zf:
                        prog = st.progress(0, text="Building ZIP...")
                        for idx, mid in enumerate(selected_in_proj):
                            prog.progress(
                                idx / len(selected_in_proj),
                                text=f"Fetching {idx+1}/{len(selected_in_proj)}...",
                            )
                            # Fallback to legacy path if not populated in DB
                            storage_path = (
                                f"projects/{proj_id}/detections/{mid}/annotated.jpg"
                            )
                            media_row = media_df[media_df["id"] == mid]
                            if not media_row.empty:
                                sp = media_row.iloc[0].get("storage_path")
                                if pd.notna(sp) and sp:
                                    storage_path = sp

                            try:
                                signed = db.create_signed_url(storage_path)
                                resp = _requests.get(signed, timeout=30)
                                resp.raise_for_status()
                                base = id_to_name.get(mid, f"{mid}.jpg")
                                arc_name = (
                                    base
                                    if base.lower().endswith((".jpg", ".jpeg", ".png"))
                                    else base + ".jpg"
                                )
                                zf.writestr(arc_name, resp.content)
                            except Exception as exc:
                                errors_dl.append(str(exc))
                        prog.progress(1.0, text="Done!")

                    if errors_dl:
                        st.warning(f"{len(errors_dl)} file(s) failed to fetch.")

                    zip_buf.seek(0)
                    safe_proj = re.sub(r"[^\w\-]", "_", name)
                    st.download_button(
                        label=f"⬇️ Download ZIP ({dl_count - len(errors_dl)} images)",
                        data=zip_buf,
                        file_name=f"{safe_proj}_detections.zip",
                        mime="application/zip",
                        type="primary",
                        width="stretch",
                        key="gal_dl_btn",
                    )

                # Delete detections option for owner
                is_owner = st.session_state.user and st.session_state.user.id == user_id
                if is_owner:
                    if st.button(
                        "🗑️ Delete Selected Detections",
                        type="secondary",
                        width="stretch",
                        key="gal_del_det",
                    ):
                        with st.spinner("Deleting selected detections..."):
                            db.delete_detections_for_media(
                                selected_in_proj, project_id=proj_id
                            )
                            st.session_state.gallery_selected -= set(selected_in_proj)
                        st.success(
                            f"✅ Cleared detections for {len(selected_in_proj)} image(s)."
                        )
                        st.session_state.img_cache_bust = int(time.time())
                        import time

                        time.sleep(1)
                        st.rerun()


# ── TAB 2: RUN AI MODEL ───────────────────────────────────────────────────────
with tab_run:
    st.subheader("Run AI Model")
    if not st.session_state.user:
        st.warning("You must be logged in to run AI models.")
    elif media_df.empty:
        st.info("Upload media first — click **⬆️ Upload Media** above.")
    else:
        v11_available = yolov11_available()
        v8seg_available = yolov8seg_available()

        model_options = []
        if v11_available:
            model_options.append("YOLOv11 - Road Damage (Detection)")
        if v8seg_available:
            model_options.append("YOLOv8 - Road Damage (Segmentation)")
        model_options.append("Mock (Demo only)")

        model_choice = st.selectbox(
            "Select AI Model",
            model_options,
            help="YOLOv11 requires best.pt in models/yolov11/weights/ · YOLOv8-seg requires best.pt in models/yolov8seg/weights/",
        )

        st.divider()

        # ── Mode toggle: new-only vs redo ─────────────────────────────────────
        run_mode = st.radio(
            "Mode",
            ["▶️ Process Pending", "🔄 Re-run (Redo)"],
            horizontal=True,
            help="**Process Pending** only shows unprocessed media. **Re-run** lets you pick already-processed media and re-run the model (old detections will be cleared first).",
        )
        is_redo = run_mode == "🔄 Re-run (Redo)"

        # Build the candidate pool
        if is_redo:
            candidate_media = media_df[media_df["status"] == "completed"]
            pool_label = "Select Processed Media to Re-run"
        else:
            candidate_media = media_df[media_df["status"] == "pending"]
            pool_label = "Select Pending Media to Process"

        if candidate_media.empty:
            if is_redo:
                st.info("No processed media to re-run yet.")
            else:
                st.info(
                    "✅ All media has already been processed. Check the 🤖 AI Detections tab, or switch to **Re-run** mode to redo them."
                )
        else:
            # Build display options grouped by batch
            media_options = {}
            batch_mapping = defaultdict(list)

            for _, row in candidate_media.iterrows():
                match = re.match(r"^(\[Batch .*?\])\s*(.*)", row["filename"])
                if match:
                    batch_id = match.group(1)
                    batch_mapping[batch_id].append(row["id"])
                else:
                    key = f"single_{row['id']}"
                    batch_mapping[key].append(row["id"])
                    media_options[key] = row["filename"]

            for batch_id, ids in batch_mapping.items():
                if not batch_id.startswith("single_"):
                    media_options[batch_id] = f"{batch_id} ({len(ids)} images)"

            selected_keys = st.multiselect(
                pool_label,
                options=list(media_options.keys()),
                format_func=lambda x: media_options[x],
                default=list(media_options.keys()),
            )

            btn_label = "🔄 Re-run AI Model" if is_redo else "▶️ Run AI Model"
            if is_redo:
                st.caption(
                    "⚠️ Existing detections and annotated images for the selected media will be permanently deleted before re-processing."
                )

            if st.button(btn_label, type="primary", width="stretch"):
                if selected_keys:
                    selected_ids = []
                    for key in selected_keys:
                        selected_ids.extend(batch_mapping[key])

                    use_yolov11 = (
                        v11_available
                        and model_choice == "YOLOv11 - Road Damage (Detection)"
                    )
                    use_yolov8seg = (
                        v8seg_available
                        and model_choice == "YOLOv8 - Road Damage (Segmentation)"
                    )
                    use_real_model = use_yolov11 or use_yolov8seg
                    chosen_model_type = (
                        ai_processor.MODEL_YOLOV8SEG
                        if use_yolov8seg
                        else ai_processor.MODEL_YOLOV11
                    )

                    # Clear old results when redoing
                    if is_redo:
                        with st.spinner("Clearing previous detections..."):
                            db.delete_detections_for_media(
                                selected_ids, project_id=proj_id
                            )

                    st.info(
                        f"🚀 Initializing AI Run: {model_choice} (Type: {chosen_model_type})"
                    )
                    progress = st.progress(0, text="Starting...")
                    errors = []

                    for i, m_id in enumerate(selected_ids):
                        progress.progress(
                            i / len(selected_ids),
                            text=f"Processing {i+1}/{len(selected_ids)}...",
                        )
                        media_row = media_df[media_df["id"] == m_id].iloc[0]

                        # Always use real model now
                        result = ai_processor.process_media(
                            media_id=m_id,
                            project_id=proj_id,
                            file_path=media_row["file_path"],
                            original_filename=media_row["filename"],
                            model_type=chosen_model_type,
                        )
                        if not result["success"]:
                            errors.append(f"{media_row['filename']}: {result['error']}")

                    progress.progress(1.0, text="Done!")

                    if errors:
                        st.warning(f"Completed with {len(errors)} error(s):")
                        for e in errors:
                            st.caption(f"⚠️ {e}")
                    else:
                        st.success(
                            f"✅ {len(selected_ids)} file(s) processed! Check the 🤖 AI Detections tab."
                        )

                    st.session_state.img_cache_bust = int(time.time())
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please select at least one media file.")


# ── TAB 3: AI DETECTIONS ─────────────────────────────────────────────────────
with tab_detections:
    if det_df.empty:
        st.info("No AI detections yet. Upload media and run the AI model first.")
    else:
        # ── Damage-type filter ────────────────────────────────────────────────
        all_types = sorted(det_df["damage_type"].dropna().unique().tolist())
        selected_types = st.multiselect(
            "🔎 Filter by Damage Type",
            options=all_types,
            default=all_types,
            help="Select which damage types to display in the results below.",
        )
        filtered_det_df = (
            det_df[det_df["damage_type"].isin(selected_types)]
            if selected_types
            else det_df
        )

        st.divider()

        # ── Delete controls (owner only) ──────────────────────────────────────
        is_owner = st.session_state.user and st.session_state.user.id == user_id
        completed_groups = {
            gk: rows
            for gk, rows in media_groups.items()
            if any(r["status"] == "completed" for r in rows)
        }
        group_display = {
            gk: (
                rows[0]["filename"]
                if gk.startswith("single_")
                else f"{gk} ({len(rows)} images)"
            )
            for gk, rows in completed_groups.items()
        }
        if is_owner:
            with st.expander("🗑️ Delete Detections", expanded=False):
                st.caption(
                    "Deleting detections removes results from the database and annotated images from Storage, then resets the media back to *pending* so it can be re-processed."
                )

                if completed_groups:
                    del_keys = st.multiselect(
                        "Select uploads to clear detections for",
                        options=list(completed_groups.keys()),
                        format_func=lambda x: group_display[x],
                        default=[],
                        key="del_det_multiselect",
                    )
                    col_del1, col_del2 = st.columns(2)
                    with col_del1:
                        if st.button(
                            "🗑️ Delete Selected Detections",
                            type="secondary",
                            width="stretch",
                            disabled=not del_keys,
                        ):
                            ids_to_clear = []
                            for gk in del_keys:
                                ids_to_clear.extend(
                                    [r["id"] for r in completed_groups[gk]]
                                )
                            with st.spinner("Deleting detections..."):
                                db.delete_detections_for_media(
                                    ids_to_clear, project_id=proj_id
                                )
                            st.success(
                                f"✅ Cleared detections for {len(del_keys)} upload(s)."
                            )
                            time.sleep(1)
                            st.rerun()
                    with col_del2:
                        all_completed_ids = [
                            r["id"] for rows in completed_groups.values() for r in rows
                        ]
                        if st.button(
                            "💣 Delete ALL Detections", type="primary", width="stretch"
                        ):
                            with st.spinner(
                                "Deleting all detections for this project..."
                            ):
                                db.delete_detections_for_media(
                                    all_completed_ids, project_id=proj_id
                                )
                            st.success(
                                "✅ All detections cleared. Media reset to pending."
                            )
                            time.sleep(1)
                            st.rerun()
                else:
                    st.info("No processed media found.")

        st.divider()

        # ── Detections by upload ──────────────────────────────────────────────
        st.subheader("Detections by Upload")

        any_shown = False
        for group_key, rows in media_groups.items():
            group_media_ids = [r["id"] for r in rows]
            group_det = filtered_det_df[
                filtered_det_df["media_id"].isin(group_media_ids)
            ]
            if group_det.empty:
                continue
            any_shown = True

            label = (
                f"📄 {rows[0]['filename']}"
                if group_key.startswith("single_")
                else f"📂 {group_key} ({len(rows)} images)"
            )

            with st.expander(label, expanded=True):
                summary = (
                    group_det.groupby("damage_type")
                    .size()
                    .reset_index(name="count")
                    .sort_values("count", ascending=False)
                )

                col_tbl, col_chart = st.columns([1, 1])
                with col_tbl:
                    st.dataframe(
                        summary,
                        hide_index=True,
                        width="stretch",
                        column_config={
                            "damage_type": "Distress Type",
                            "count": st.column_config.NumberColumn("Occurrences"),
                        },
                    )
                with col_chart:
                    st.bar_chart(summary.set_index("damage_type")["count"])

        if not any_shown:
            st.info("No detections match the selected damage types.")

        st.divider()

        # ── Project summary (uses filtered data) ──────────────────────────────
        st.subheader("📊 Project Summary")
        m1, m2, m3, m4 = st.columns(4)
        processed_count = len(media_df[media_df["status"] == "completed"])
        det_count = len(filtered_det_df)
        density = (det_count / processed_count) if processed_count > 0 else 0.0

        primary_distress = "None"
        if not filtered_det_df.empty:
            primary_distress = filtered_det_df["damage_type"].value_counts().idxmax()
            primary_distress = str(primary_distress).replace("_", " ").title()

        m1.metric("Images Analyzed", processed_count)
        m2.metric("Total Distresses", det_count)
        m3.metric("Distress Density", f"{density:.1f} per img")
        m4.metric("Primary Distress", primary_distress)

        st.markdown("**Distress Type Distribution — All Media**")
        proj_summary = (
            filtered_det_df.groupby("damage_type")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        col_ps1, col_ps2 = st.columns([1, 1])
        with col_ps1:
            st.dataframe(
                proj_summary,
                hide_index=True,
                width="stretch",
                column_config={
                    "damage_type": "Distress Classification",
                    "count": st.column_config.NumberColumn("Occurrences"),
                },
            )
        with col_ps2:
            st.bar_chart(proj_summary.set_index("damage_type")["count"])
