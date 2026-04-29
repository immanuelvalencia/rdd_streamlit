"""
Real AI Processor
=================
Replaces mock_ai.py when the YOLO11 model is available.

Workflow per media item:
  1. Download raw image from Supabase Storage (via signed URL)
  2. Run YOLO11 inference
  3. Save detections to the `detections` table
  4. Upload the annotated image to  projects/<project_id>/detections/<media_id>/annotated.jpg
  5. Mark media status as 'completed'
"""

import logging
import requests

import database as db
from ai.yolov11_inference import run_inference, is_model_available

logger = logging.getLogger(__name__)


def process_media(media_id: str, project_id: str, file_path: str) -> dict:
    """
    Runs real YOLO11 inference on a single media file stored in Supabase Storage.

    Args:
        media_id:   UUID of the media record
        project_id: UUID of the parent project
        file_path:  Supabase public/stored URL for the raw image

    Returns:
        dict with keys: success (bool), detections (list), error (str|None)
    """
    try:
        # 1. Download the raw image
        signed_url = db.create_signed_url(file_path)
        response = requests.get(signed_url, timeout=30)
        response.raise_for_status()
        image_bytes = response.content

        # 2. Run YOLO11 inference
        detections, annotated_bytes = run_inference(image_bytes)

        # 3. Save each detection to the database
        for det in detections:
            db.add_detection(media_id, det["damage_type"], det["confidence"])

        # 4. Upload the annotated image to the detections/ folder
        db.upload_detection_file(
            project_id=project_id,
            media_id=media_id,
            filename="annotated.jpg",
            file_bytes=annotated_bytes,
            content_type="image/jpeg",
        )

        # 5. Mark media as completed
        db.update_media_status(media_id, "completed")

        logger.info(f"[{media_id}] Processed — {len(detections)} detection(s)")
        return {"success": True, "detections": detections, "error": None}

    except Exception as e:
        logger.error(f"[{media_id}] Processing failed: {e}")
        db.update_media_status(media_id, "failed")
        return {"success": False, "detections": [], "error": str(e)}


def process_batch(media_records: list[dict]) -> list[dict]:
    """
    Processes a list of media records.

    Each record must have: id, project_id, file_path
    Returns a list of result dicts (one per media item).
    """
    results = []
    for record in media_records:
        result = process_media(
            media_id=record["id"],
            project_id=record["project_id"],
            file_path=record["file_path"],
        )
        result["media_id"] = record["id"]
        results.append(result)
    return results
