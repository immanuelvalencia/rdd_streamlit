import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os

PHILIPPINES_LOCATIONS = {
    "NCR": {
        "Metro Manila": [
            "Manila", "Quezon City", "Caloocan", "Las Piñas", "Makati", "Malabon", 
            "Mandaluyong", "Marikina", "Muntinlupa", "Navotas", "Parañaque", 
            "Pasay", "Pasig", "San Juan", "Taguig", "Valenzuela", "Pateros"
        ]
    },
    "Region III": {
        "Aurora": [
            "Baler", "Casiguran", "Dilasag", "Dinalungan", "Dingalan", 
            "Dipaculao", "Maria Aurora", "San Luis"
        ],
        "Bataan": [
            "Balanga City", "Abucay", "Bagac", "Dinalupihan", "Hermosa", 
            "Limay", "Mariveles", "Morong", "Orani", "Orion", "Pilar", "Samal"
        ],
        "Bulacan": [
            "Malolos City", "Meycauayan City", "San Jose del Monte City", "Angat", 
            "Balagtas", "Baliuag", "Bocaue", "Bulakan", "Bustos", "Calumpit", 
            "Doña Remedios Trinidad", "Guiguinto", "Hagonoy", "Marilao", "Norzagaray", 
            "Obando", "Pandi", "Paombong", "Plaridel", "Pulilan", "San Ildefonso", 
            "San Miguel", "San Rafael", "Santa Maria"
        ],
        "Nueva Ecija": [
            "Cabanatuan City", "Gapan City", "Palayan City", "San Jose City", 
            "Science City of Muñoz", "Aliaga", "Bongabon", "Cabiao", "Carranglan", 
            "Cuyapo", "Gabaldon", "General Mamerto Natividad", "General Tinio", 
            "Guimba", "Jaen", "Laur", "Licab", "Llanera", "Lupao", "Nampicuan", 
            "Pantabangan", "Peñaranda", "Quezon", "Rizal", "San Antonio", "San Isidro", 
            "San Leonardo", "Santa Rosa", "Santo Domingo", "Talavera", "Talugtug", "Zaragoza"
        ],
        "Pampanga": [
            "Angeles City", "Mabalacat City", "San Fernando City", "Apalit", "Arayat", 
            "Bacolor", "Candaba", "Floridablanca", "Guagua", "Lubao", "Macabebe", 
            "Masantol", "Mexico", "Minalin", "Porac", "San Luis", "San Simon", 
            "Santa Ana", "Santa Rita", "Santo Tomas", "Sasmuan"
        ],
        "Tarlac": [
            "Tarlac City", "Anao", "Bamban", "Camiling", "Capas", "Concepcion", 
            "Gerona", "La Paz", "Mayantoc", "Moncada", "Paniqui", "Pura", "Ramos", 
            "San Clemente", "San Jose", "San Manuel", "Santa Ignacia", "Victoria"
        ],
        "Zambales": [
            "Olongapo City", "Botolan", "Cabangan", "Candelaria", "Castillejos", 
            "Iba", "Masinloc", "Palauig", "San Antonio", "San Felipe", "San Marcelino", 
            "San Narciso", "Santa Cruz", "Subic"
        ]
    },
    "Region IV-A": {
        "Rizal": [
            "Antipolo City", "Angono", "Baras", "Binangonan", "Cainta", "Cardona", 
            "Jalajala", "Morong", "Pililla", "Rodriguez (Montalban)", "San Mateo", 
            "Tanay", "Taytay", "Teresa"
        ],
        "Cavite": [
            "Bacoor City", "Cavite City", "Dasmariñas City", "General Trias City", 
            "Imus City", "Tagaytay City", "Trece Martires City", "Alfonso", "Amadeo", 
            "Carmona", "General Emilio Aguinaldo", "General Mariano Alvarez", "Indang", 
            "Kawit", "Magallanes", "Maragondon", "Mendez", "Naic", "Noveleta", 
            "Rosario", "Silang", "Tanza", "Ternate"
        ],
        "Laguna": [
            "Biñan City", "Cabuyao City", "Calamba City", "San Pablo City", 
            "San Pedro City", "Santa Rosa City", "Alaminos", "Bay", "Cabalantian", 
            "Calauan", "Cavinti", "Famy", "Kalayaan", "Liliw", "Los Baños", 
            "Luisiana", "Lumban", "Mabitac", "Magdalena", "Majayjay", "Nagcarlan", 
            "Paete", "Pagsanjan", "Pakil", "Pangil", "Pila", "Rizal", "Santa Cruz", 
            "Santa Maria", "Siniloan", "Victoria"
        ],
        "Batangas": [
            "Batangas City", "Lipa City", "Santo Tomas City", "Tanauan City", 
            "Agoncillo", "Alitagtag", "Balayan", "Balete", "Bauan", "Calaca", 
            "Calatagan", "Cuenca", "Ibaan", "Laurel", "Lemery", "Lian", "Lobo", 
            "Mabini", "Malvar", "Mataasnakahoy", "Nasugbu", "Padre Garcia", "Rosario", 
            "San Jose", "San Juan", "San Luis", "San Nicolas", "San Pascual", 
            "Santa Teresita", "Taal", "Talisay", "Taysan", "Tingloy", "Tuy"
        ],
        "Quezon": [
            "Lucena City", "Tayabas City", "Agdangan", "Alabat", "Atimonan", 
            "Buenavista", "Burdeos", "Calauag", "Candelaria", "Cateel", "Dolores", 
            "General Luna", "General Nakar", "Guinayangan", "Gumaca", "Infanta", 
            "Jomalig", "Lopez", "Lucban", "Macalelon", "Mauban", "Mulanay", 
            "Padre Burgos", "Pagbilao", "Panukulan", "Patnanungan", "Perez", "Pitogo", 
            "Plaridel", "Polillo", "Quezon", "Real", "Sampaloc", "San Andres", 
            "San Antonio", "San Francisco", "San Narciso", "Sariaya", "Tagkawayan", "Unisan"
        ]
    },
    "Region VII": {
        "Cebu": [
            "Cebu City", "Lapu-Lapu City", "Mandaue City", "Talisay City", 
            "Toledo City", "Bogo City", "Carcar City", "Danao City", "Naga City", 
            "Alcantara", "Alcoy", "Alegria", "Aloguinsan", "Argao", "Asturias", 
            "Badian", "Balamban", "Bantayan", "Barili", "Bogo", "Boljoon", "Borbon", 
            "Carmen", "Catmon", "Compostela", "Consolacion", "Cordova", "Daanbantayan", 
            "Dalaguete", "Dumanjug", "Ginatilan", "Liloan", "Madridejos", "Malabuyoc", 
            "Medellin", "Minglanilla", "Moalboal", "Nagcarlan", "Oslob", "Pilar", 
            "Pinamungajan", "Poro", "Ronda", "Samboan", "San Fernando", "San Francisco", 
            "San Remigio", "Santa Fe", "Santander", "Sibonga", "Sogod", "Tabuelan", 
            "Tabogon", "Tuburan", "Tudela"
        ],
        "Bohol": [
            "Tagbilaran City", "Alburquerque", "Alicia", "Ander", "Antequera", 
            "Baclayon", "Balilihan", "Batuan", "Bien Unido", "Bilar", "Buenavista", 
            "Calape", "Candijay", "Carmen", "Catigbian", "Clarin", "Corella", "Cortes", 
            "Dagohoy", "Danao", "Dauis", "Dimiao", "Duero", "Garcia Hernandez", 
            "Getafe", "Guindulman", "Inabanga", "Jagna", "Lila", "Loay", "Loboc", 
            "Loon", "Mabini", "Maribojoc", "Panglao", "Pilar", "President Carlos P. Garcia", 
            "Sagbayan", "San Isidro", "San Miguel", "Sevilla", "Sierra Bullones", 
            "Sikatuna", "Talibon", "Trinidad", "Tubigon", "Ubay", "Valencia"
        ],
        "Negros Oriental": [
            "Bais City", "Bayawan City", "Canlaon City", "Dumaguete City", 
            "Guihulngan City", "Tanjay City", "Amlan", "Ayungon", "Bacong", "Basay", 
            "Bindoy", "Dauin", "Gigalangan", "Jimalalud", "La Libertad", "Mabinay", 
            "Manjuyod", "Pampona", "San Jose", "Siaton", "Sibulan", "Tayasan", 
            "Valencia", "Vallehermoso", "Zamboanguita"
        ],
        "Siquijor": [
            "Enrique Villanueva", "Larena", "Lazi", "Maria", "San Juan", "Siquijor"
        ]
    },
    "Region XI": {
        "Davao del Sur": [
            "Davao City", "Digos City", "Bansalan", "Hagonoy", "Kiblawan", 
            "Magsaysay", "Malalag", "Padada", "Santa Cruz", "Sulop"
        ],
        "Davao del Norte": [
            "Panabo City", "Samal City (Island Garden City of Samal)", "Tagum City", 
            "Asuncion", "Carmen", "Kapalong", "New Corella", "San Isidro", 
            "Santo Tomas", "Talaingod"
        ],
        "Davao de Oro": [
            "Compostela", "Laak", "Mabini", "Maco", "Maragusan", "Mawab", 
            "Monkayo", "Montevista", "Nabunturan", "New Bataan", "Pantukan"
        ],
        "Davao Oriental": [
            "Mati City", "Baganga", "Banaybanay", "Boston", "Caraga", "Cateel", 
            "Governor Generoso", "Lupon", "Manay", "San Isidro", "Tarragona"
        ],
        "Davao Occidental": [
            "Don Marcelino", "Jose Abad Santos", "Malita", "Santa Maria", "Sarangani"
        ]
    }
}


@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except FileNotFoundError:
        st.error(
            "⚠️ .streamlit/secrets.toml is missing! Please create it with your SUPABASE_URL and SUPABASE_KEY."
        )
        st.stop()
    except KeyError as e:
        st.error(
            f"⚠️ Missing secret: {e}. Please add it to your .streamlit/secrets.toml."
        )
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
            profile = get_profile(session.user.id) or {
                "name": "Unknown",
                "position": "Unknown",
            }
            return session.user, profile
    except Exception:
        pass
    return None, None


# --- Auth ---


def sign_up(email, password, name, position, institution=""):
    supabase = init_connection()
    res = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
            "options": {
                "data": {"name": name, "position": position, "institution": institution}
            },
        }
    )
    if res and res.user:
        try:
            update_data = {"name": name, "position": position}
            if institution:
                update_data["institution"] = institution
            supabase.table("profiles").update(update_data).eq(
                "id", res.user.id
            ).execute()
        except Exception:
            pass
    return res


def reset_password(email):
    supabase = init_connection()
    return supabase.auth.reset_password_email(email)


def get_profile(user_id):
    supabase = init_connection()
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
    except Exception:
        pass
    return None


def update_profile(user_id, name, position, institution):
    supabase = init_connection()
    supabase.table("profiles").update(
        {"name": name, "position": position, "institution": institution}
    ).eq("id", user_id).execute()


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
    marker = f"/{STORAGE_BUCKET}/"
    if file_path.startswith("http") and marker in file_path:
        return file_path.split(marker, 1)[1].split("?")[0]
    return file_path


# --- Projects ---


def add_project(name, region, province, city, street, latitude, longitude, user_id):
    supabase = init_connection()
    data = {
        "name": name,
        "region": region,
        "location": province,  # Store province in the location column
        "city": city,
        "street": street,
        "latitude": latitude,
        "longitude": longitude,
        "user_id": user_id,
    }
    supabase.table("projects").insert(data).execute()


def get_projects():
    # Public access: Fetch all projects
    supabase = init_connection()
    proj_resp = (
        supabase.table("projects").select("*").order("created_at", desc=True).execute()
    )
    proj_df = pd.DataFrame(proj_resp.data)

    if proj_df.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "name",
                "province",
                "region",
                "city",
                "street",
                "latitude",
                "longitude",
                "user_id",
                "created_at",
                "creator_email",
            ]
        )

    # Rename location column to province
    if "location" in proj_df.columns:
        proj_df = proj_df.rename(columns={"location": "province"})

    prof_resp = supabase.table("profiles").select("id, email, name").execute()
    prof_df = pd.DataFrame(prof_resp.data).rename(
        columns={"id": "user_id", "email": "creator_email", "name": "creator_name"}
    )

    if not prof_df.empty:
        proj_df = pd.merge(proj_df, prof_df, on="user_id", how="left")
    else:
        proj_df["creator_email"] = "Unknown"

    return proj_df


def delete_project(project_id):
    supabase = init_connection()

    # 1. Collect all storage paths from media records before deleting them
    media_resp = (
        supabase.table("media")
        .select("file_path")
        .eq("project_id", project_id)
        .execute()
    )
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
        for f in det_files or []:
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


def upload_to_storage(
    storage_path: str, file_bytes: bytes, content_type: str = "application/octet-stream"
) -> str:
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
        res = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
            storage_path, expires_in
        )
        # supabase-py v2 returns a dict with 'signedURL'
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signed_url") or file_path
        return str(res) if res else file_path
    except Exception:
        return file_path  # fallback to original URL


def upload_detection_file(
    project_id: str,
    original_filename: str,
    model_name: str,
    file_bytes: bytes,
    content_type: str = "image/jpeg",
) -> str:
    """
    Uploads a detection result file to:
      projects/<project_id>/annotated/<model_name>/<filename>_<model_name>.<ext>
    Returns the public URL.
    """
    import re

    # Remove [Batch xxx] prefix if present
    clean_name = re.sub(r"^\[Batch \d+\]\s*", "", original_filename)

    if "." in clean_name:
        base_name, ext = clean_name.rsplit(".", 1)
        new_filename = f"{base_name}_{model_name}.{ext}"
    else:
        new_filename = f"{clean_name}_{model_name}.jpg"

    storage_path = f"projects/{project_id}/annotated/{model_name}/{new_filename}"
    return upload_to_storage(storage_path, file_bytes, content_type)


# --- Media ---


def _content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime",
    }.get(ext, "application/octet-stream")


def _sanitize_storage_name(filename: str) -> str:
    """
    Returns a storage-safe filename:
    - Strips the [Batch xxx] display prefix
    - Replaces spaces and special chars with underscores
    """
    import re

    # Remove [Batch xxx] prefix added for UI grouping
    clean = re.sub(r"^\[Batch \d+\]\s*", "", filename)
    # Replace spaces and any characters that aren't alphanumeric, dash, dot, or underscore
    clean = re.sub(r"[^\w.\-]", "_", clean)
    return clean


def add_media(
    project_id: str, filename: str, file_bytes: bytes, sub_folder: str = None
) -> str:
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
    record = {
        "project_id": project_id,
        "filename": filename,
        "file_path": "",
        "status": "pending",
    }
    response = supabase.table("media").insert(record).execute()
    media_id = response.data[0]["id"]

    # 2. Build a safe storage key (no brackets, spaces, or special chars)
    safe_filename = _sanitize_storage_name(filename)
    folder = sub_folder if sub_folder else media_id
    storage_path = f"projects/{project_id}/raw/{folder}/{safe_filename}"

    # 3. Upload to Supabase Storage
    public_url = upload_to_storage(
        storage_path, file_bytes, _content_type(safe_filename)
    )

    # 4. Update the record with the public URL
    supabase.table("media").update(
        {
            "file_path": public_url,
        }
    ).eq("id", media_id).execute()

    return media_id


def get_media_for_project(project_id):
    supabase = init_connection()
    response = (
        supabase.table("media")
        .select("*")
        .eq("project_id", project_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    df = pd.DataFrame(response.data)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "id",
                "project_id",
                "filename",
                "file_path",
                "status",
                "uploaded_at",
            ]
        )
    return df


def update_media_status(media_id, status, annotated_url=None):
    supabase = init_connection()
    update_data = {"status": status}
    if annotated_url:
        update_data["storage_path"] = annotated_url
    supabase.table("media").update(update_data).eq("id", media_id).execute()


def delete_media_batch(media_ids):
    if not media_ids:
        return
    supabase = init_connection()

    # 1. Collect all storage paths to delete raw files and detection files
    resp = (
        supabase.table("media")
        .select("id, file_path, project_id")
        .in_("id", media_ids)
        .execute()
    )
    storage_paths = []
    for m in resp.data:
        fp = m.get("file_path", "")
        pid = m.get("project_id", "")
        mid = m.get("id", "")
        if fp:
            path = _extract_storage_path(fp)
            if path:
                storage_paths.append(path)
        if pid and mid:
            # Also try to delete the annotated image
            storage_paths.append(f"projects/{pid}/detections/{mid}/annotated.jpg")

    if storage_paths:
        try:
            supabase.storage.from_(STORAGE_BUCKET).remove(storage_paths)
        except Exception:
            pass

    # 2. Delete the DB records
    supabase.table("media").delete().in_("id", media_ids).execute()


# --- Detections ---


def add_detection(media_id, damage_type, confidence):
    supabase = init_connection()
    data = {"media_id": media_id, "damage_type": damage_type, "confidence": confidence}
    supabase.table("detections").insert(data).execute()


def delete_detections_for_media(media_ids: list, project_id: str = None):
    """
    Deletes all detection rows for the given media IDs, removes annotated
    images from Storage (if project_id provided), and resets media status
    back to 'pending' so they can be re-processed.
    """
    if not media_ids:
        return
    supabase = init_connection()

    # Remove annotated images from Storage (legacy and new)
    if project_id:
        paths_to_remove = []
        # Legacy paths
        for mid in media_ids:
            paths_to_remove.append(
                f"projects/{project_id}/detections/{mid}/annotated.jpg"
            )

        # For the new paths, we need to find them from the DB first
        res = (
            supabase.table("media")
            .select("storage_path")
            .in_("id", media_ids)
            .execute()
        )
        for r in res.data:
            sp = r.get("storage_path")
            if sp:
                # Extract relative path from URL or use as is
                extracted = _extract_storage_path(sp)
                if extracted:
                    paths_to_remove.append(extracted)

        if paths_to_remove:
            try:
                supabase.storage.from_(STORAGE_BUCKET).remove(paths_to_remove)
            except Exception:
                pass  # non-fatal

    # Delete detection rows
    supabase.table("detections").delete().in_("media_id", media_ids).execute()

    # Reset media status back to pending
    supabase.table("media").update({"status": "pending"}).in_("id", media_ids).execute()


def get_all_analytics():
    # Public access: Fetch all analytics
    supabase = init_connection()

    projects_resp = (
        supabase.table("projects")
        .select("id, name, street, city, region, location, latitude, longitude")
        .execute()
    )
    media_resp = supabase.table("media").select("id, project_id, status").execute()
    detections_resp = (
        supabase.table("detections")
        .select("media_id, damage_type, confidence")
        .execute()
    )

    proj_df = pd.DataFrame(projects_resp.data)
    media_df = pd.DataFrame(media_resp.data)
    det_df = pd.DataFrame(detections_resp.data)

    if proj_df.empty:
        return pd.DataFrame(
            columns=[
                "project_id",
                "project_name",
                "street",
                "city",
                "province",
                "region",
                "latitude",
                "longitude",
                "media_id",
                "status",
                "damage_type",
                "confidence",
            ]
        )

    proj_df = proj_df.rename(columns={"id": "project_id", "name": "project_name"})
    if "location" in proj_df.columns:
        proj_df = proj_df.rename(columns={"location": "province"})

    if media_df.empty:
        df = proj_df
        df["media_id"] = None
        df["status"] = None
        df["damage_type"] = None
        df["confidence"] = None
        return df

    media_df = media_df.rename(columns={"id": "media_id"})
    merged_df = pd.merge(proj_df, media_df, on="project_id", how="left")

    if det_df.empty:
        merged_df["damage_type"] = None
        merged_df["confidence"] = None
        return merged_df

    final_df = pd.merge(merged_df, det_df, on="media_id", how="left")
    return final_df
