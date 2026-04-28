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
    supabase.table("projects").delete().eq("id", project_id).execute()

# --- Media ---

def add_media(project_id, filename, file_path):
    supabase = init_connection()
    data = {"project_id": project_id, "filename": filename, "file_path": file_path, "status": "pending"}
    response = supabase.table("media").insert(data).execute()
    return response.data[0]['id']

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
