import time
import random
import database as db

DAMAGE_TYPES = [
    "pothole", 
    "alligator cracking", 
    "longitudinal crack",
    "transverse crack",
    "rutting"
]

def process_media(media_id):
    """
    Simulates the AI processing for a given media file.
    1. Updates status to 'completed'.
    2. Generates 1-3 random damage detections.
    3. Saves them to the database.
    """
    # Simulate processing delay (Streamlit is synchronous, keep it short for UI responsiveness)
    time.sleep(1.5)
    
    # Generate random number of detections
    num_detections = random.randint(1, 3)
    
    for _ in range(num_detections):
        damage_type = random.choice(DAMAGE_TYPES)
        confidence = round(random.uniform(0.5, 0.99), 2)
        db.add_detection(media_id, damage_type, confidence)
        
    # Mark as completed
    db.update_media_status(media_id, 'completed')
