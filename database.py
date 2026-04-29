import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os

@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except FileNotFoundError:
        st.error("⚠️ .streamlit/secrets.toml is missing! Please create it with your SUPABASE_URL and SUPABASE_KEY.")
        st.stop()
    except KeyError as e:
        st.error(f"⚠️ Missing secret: {e}. Please add it to your .streamlit/secrets.toml.")
        st.stop()

def init_db():
    _ = init_connection()

def restore_session():
    """
    Tries to recover the active auth session from the cached Supabase client.
    Because the client is @st.cache_resource, it survives browser refreshes on
    the same server process and still holds the last signed-in session.
    Returns (user, profile) or (None, None) if no active session.
    """
    try:
        supabase = init_connection()
        session = supabase.auth.get_session()
        if session and session.user:
            profile = get_profile(session.user.id) or {"name": "Unknown", "position": "Unknown"}
            return session.user, profile
    except Exception:
        pass
    return None, None

# --- Auth ---

def sign_up(email, password, name, position):
    supabase = init_connection()
    res = supabase.auth.sign_up({
        "email": email, 
        "password": password,
        "options": {
            "data": {
                "name": name,
                "position": position
            }
        }
    })
    if res and res.user:
        try:
            supabase.table("profiles").update({
                "name": name, 
                "position": position
            }).eq("id", res.user.id).execute()
        except Exception:
            pass
    return res

def get_profile(user_id):
    supabase = init_connection()
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
    except Exception:
        pass
    return None

def update_profile(user_id, name, position):
    supabase = init_connection()
    supabase.table("profiles").update({"name": name, "position": position}).eq("id", user_id).execute()

def sign_in(email, password):
    supabase = init_connection()
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out():
    supabase = init_connection()
    return supabase.auth.sign_out()

# --- Storage constants (used across Projects and Storage sections) ---

STORAGE_BUCKET = "rdd_media"

def _extract_storage_path(file_path: str) -> str:
    """Extract the bucket-relative storage path from a full Supabase URL or return as-is."""
    marker = f'/{STORAGE_BUCKET}/'
    if file_path.startswith('http') and marker in file_path:
        return file_path.split(marker, 1)[1].split('?')[0]
    return file_path

# --- Projects ---

def add_project(name, region, city, street, latitude, longitude, user_id):
    supabase = init_connection()
    data = {
        "name": name, 
        "region": region,
        "city": city,
        "street": street,
        "latitude": latitude,
        "longitude": longitude,
        "user_id": user_id
    }
    supabase.table("projects").insert(data).execute()

def get_projects():
    # Public access: Fetch all projects
    supabase = init_connection()
    proj_resp = supabase.table("projects").select("*").order("created_at", desc=True).execute()
    proj_df = pd.DataFrame(proj_resp.data)
    
    if proj_df.empty:
        return pd.DataFrame(columns=["id", "name", "region", "city", "street", "latitude", "longitude", "user_id", "created_at", "creator_email"])
        
    prof_resp = supabase.table("profiles").select("id, email, name").execute()
    prof_df = pd.DataFrame(prof_resp.data).rename(columns={"id": "user_id", "email": "creator_email", "name": "creator_name"})
    
    if not prof_df.empty:
        proj_df = pd.merge(proj_df, prof_df, on="user_id", how="left")
    else:
        proj_df["creator_email"] = "Unknown"
        
    return proj_df

def delete_project(project_id):
    supabase = init_connection()

    # 1. Collect all storage paths from media records before deleting them
    media_resp = supabase.table("media").select("file_path").eq("project_id", project_id).execute()
    storage_paths = []
    for m in media_resp.data:
        fp = m.get("file_path", "")
        if fp:
            path = _extract_storage_path(fp)
            if path:
                storage_paths.append(path)

    # 2. Also list everything under projects/<project_id>/detections/ in case
    #    real annotated outputs were written there
    try:
        det_files = supabase.storage.from_(STORAGE_BUCKET).list(
            f"projects/{project_id}/detections", {"limit": 1000}
        )
        for f in (det_files or []):
            storage_paths.append(f"projects/{project_id}/detections/{f['name']}")
    except Exception:
        pass  # non-fatal if the folder doesn't exist yet

    # 3. Batch-delete all storage files (Supabase accepts a list of paths)
    if storage_paths:
        try:
            supabase.storage.from_(STORAGE_BUCKET).remove(storage_paths)
        except Exception:
            pass  # log but don't block project deletion

    # 4. Delete the DB record (cascade removes media + detections rows)
    supabase.table("projects").delete().eq("id", project_id).execute()


# --- Storage ---

def upload_to_storage(storage_path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Uploads bytes to rdd_media bucket at the given path.
    Returns the public URL of the uploaded file.
    Folder structure: projects/<project_id>/raw/<sub_folder>/<filename>
    """
    supabase = init_connection()
    supabase.storage.from_(STORAGE_BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    # Store the raw storage path as the URL placeholder;
    # callers should use create_signed_url() to get a displayable URL.
    res = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
    return res

def create_signed_url(file_path: str, expires_in: int = 3600) -> str:
    """
    Creates a signed URL for a file — works for both public and private buckets.
    Accepts a full Supabase storage URL or a raw storage path.
    """
    supabase = init_connection()
    storage_path = _extract_storage_path(file_path)
    try:
        res = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(storage_path, expires_in)
        # supabase-py v2 returns a dict with 'signedURL'
        if isinstance(res, dict):
            return res.get('signedURL') or res.get('signed_url') or file_path
        return str(res) if res else file_path
    except Exception:
        return file_path  # fallback to original URL

def upload_detection_file(project_id: str, media_id: str, filename: str, file_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """
    Uploads a detection result file (annotated image, JSON, etc.) to:
      projects/<project_id>/detections/<media_id>/<filename>
    Returns the public URL.
    """
    storage_path = f"projects/{project_id}/detections/{media_id}/{filename}"
    return upload_to_storage(storage_path, file_bytes, content_type)

# --- Media ---

def _content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "mp4": "video/mp4", "avi": "video/x-msvideo", "mov": "video/quicktime",
    }.get(ext, "application/octet-stream")

def _sanitize_storage_name(filename: str) -> str:
    """
    Returns a storage-safe filename:
    - Strips the [Batch xxx] display prefix
    - Replaces spaces and special chars with underscores
    """
    import re
    # Remove [Batch xxx] prefix added for UI grouping
    clean = re.sub(r'^\[Batch \d+\]\s*', '', filename)
    # Replace spaces and any characters that aren't alphanumeric, dash, dot, or underscore
    clean = re.sub(r'[^\w.\-]', '_', clean)
    return clean

def add_media(project_id: str, filename: str, file_bytes: bytes, sub_folder: str = None) -> str:
    """
    Uploads file to Supabase Storage and inserts a media record.

    The `filename` stored in the DB may contain a '[Batch xxx]' prefix for UI grouping.
    The actual storage key always uses a sanitized version of the base filename.

    Storage path:
      - Single file:  projects/<project_id>/raw/<media_id>/<safe_filename>
      - Batch images: projects/<project_id>/raw/<sub_folder>/<safe_filename>

    Returns the new media record id.
    """
    supabase = init_connection()

    # 1. Insert pending record to get the auto-generated media_id
    record = {"project_id": project_id, "filename": filename, "file_path": "", "status": "pending"}
    response = supabase.table("media").insert(record).execute()
    media_id = response.data[0]["id"]

    # 2. Build a safe storage key (no brackets, spaces, or special chars)
    safe_filename = _sanitize_storage_name(filename)
    folder = sub_folder if sub_folder else media_id
    storage_path = f"projects/{project_id}/raw/{folder}/{safe_filename}"

    # 3. Upload to Supabase Storage
    public_url = upload_to_storage(storage_path, file_bytes, _content_type(safe_filename))

    # 4. Update the record with the public URL
    supabase.table("media").update({
        "file_path": public_url,
    }).eq("id", media_id).execute()

    return media_id



def get_media_for_project(project_id):
    supabase = init_connection()
    response = supabase.table("media").select("*").eq("project_id", project_id).order("uploaded_at", desc=True).execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "project_id", "filename", "file_path", "status", "uploaded_at"])
    return df

def update_media_status(media_id, status):
    supabase = init_connection()
    supabase.table("media").update({"status": status}).eq("id", media_id).execute()

# --- Detections ---

def add_detection(media_id, damage_type, confidence):
    supabase = init_connection()
    data = {"media_id": media_id, "damage_type": damage_type, "confidence": confidence}
    supabase.table("detections").insert(data).execute()

def get_all_analytics():
    # Public access: Fetch all analytics
    supabase = init_connection()
    
    projects_resp = supabase.table("projects").select("id, name").execute()
    media_resp = supabase.table("media").select("id, project_id, status").execute()
    detections_resp = supabase.table("detections").select("media_id, damage_type, confidence").execute()
    
    proj_df = pd.DataFrame(projects_resp.data)
    media_df = pd.DataFrame(media_resp.data)
    det_df = pd.DataFrame(detections_resp.data)
    
    if proj_df.empty:
        return pd.DataFrame(columns=['project_id', 'project_name', 'media_id', 'status', 'damage_type', 'confidence'])
        
    proj_df = proj_df.rename(columns={"id": "project_id", "name": "project_name"})
    
    if media_df.empty:
        df = proj_df
        df['media_id'] = None
        df['status'] = None
        df['damage_type'] = None
        df['confidence'] = None
        return df
        
    media_df = media_df.rename(columns={"id": "media_id"})
    merged_df = pd.merge(proj_df, media_df, on="project_id", how="left")
    
    if det_df.empty:
        merged_df['damage_type'] = None
        merged_df['confidence'] = None
        return merged_df
        
    final_df = pd.merge(merged_df, det_df, on="media_id", how="left")
    return final_df
