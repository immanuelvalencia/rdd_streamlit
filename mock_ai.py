import time
import random
import requests
import database as db

DAMAGE_TYPES = [
    "pothole", 
    "alligator_crack", 
    "cracks",
    "pumping_and_depression"
]

def process_media(media_id):
    """
    Simulates the AI processing for a given media file.
    1. Updates status to 'completed'.
    2. Generates 1-3 random damage detections.
    3. Saves them to the database.
    4. Mocks an annotated image upload by using the original image.
    """
    # Simulate processing delay
    time.sleep(1.5)
    
    # 1. Fetch media info to get project_id and file_path
    supabase = db.init_connection()
    resp = supabase.table("media").select("project_id, file_path").eq("id", media_id).execute()
    if not resp.data:
        return
    
    project_id = resp.data[0]["project_id"]
    file_path = resp.data[0]["file_path"]

    # 2. Generate random detections
    num_detections = random.randint(1, 3)
    for _ in range(num_detections):
        damage_type = random.choice(DAMAGE_TYPES)
        confidence = round(random.uniform(0.5, 0.99), 2)
        db.add_detection(media_id, damage_type, confidence)
        
    # 3. Mock annotated image (just copy the original bytes for the demo)
    try:
        signed_url = db.create_signed_url(file_path)
        img_resp = requests.get(signed_url, timeout=10)
        if img_resp.status_code == 200:
            db.upload_detection_file(
                project_id=project_id,
                media_id=media_id,
                filename="annotated.jpg",
                file_bytes=img_resp.content
            )
    except Exception:
        pass

    # 4. Mark as completed
    db.update_media_status(media_id, 'completed')

