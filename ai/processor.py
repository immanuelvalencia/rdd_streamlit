"""
Real AI Processor
=================

Workflow per media item:
  1. Download raw image from Supabase Storage (via signed URL)
  2. Run inference with the chosen model (yolov11 | yolov8seg)
  3. Save detections to the `detections` table
  4. Upload the annotated image to model-specific paths
  5. Mark media status as 'completed'
"""

import logging
import requests

import database as db
from ai.yolov11_inference import (
    run_inference as run_yolov11,
    is_model_available as yolov11_available,
)
from ai.yolov8seg_inference import (
    run_inference as run_yolov8seg,
    is_model_available as yolov8seg_available,
)

logger = logging.getLogger(__name__)

MODEL_YOLOV11 = "yolov11"
MODEL_YOLOV8SEG = "yolov8seg"


def process_media(
    media_id: str,
    project_id: str,
    file_path: str,
    original_filename: str,
    model_type: str = MODEL_YOLOV11,
) -> dict:
    """
    Runs real YOLO inference on a single media file stored in Supabase Storage.

    Args:
        media_id:    UUID of the media record
        project_id:  UUID of the parent project
        file_path:   Supabase public/stored URL for the raw image
        original_filename: The original filename from the database
        model_type:  Which model to use - 'yolov11' or 'yolov8seg'

    Returns:
        dict with keys: success (bool), detections (list), error (str|None)
    """
    try:
        # 1. Download the raw image
        signed_url = db.create_signed_url(file_path)
        response = requests.get(signed_url, timeout=30)
        response.raise_for_status()
        image_bytes = response.content

        # 2. Run inference with the selected model
        if model_type == MODEL_YOLOV8SEG:
            detections, annotated_bytes = run_yolov8seg(image_bytes)
        else:
            detections, annotated_bytes = run_yolov11(image_bytes)

        # 3. Save each detection to the database
        for det in detections:
            db.add_detection(media_id, det["damage_type"], det["confidence"])

        # 4. Upload the annotated image to the new model-specific folder
        annotated_url = db.upload_detection_file(
            project_id=project_id,
            original_filename=original_filename,
            model_name=model_type,
            file_bytes=annotated_bytes,
            content_type="image/jpeg",
        )

        # 5. Mark media as completed and save the annotated path
        db.update_media_status(media_id, "completed", annotated_url)

        logger.info(
            f"[{media_id}] Processed ({model_type}) — {len(detections)} detection(s)"
        )
        return {"success": True, "detections": detections, "error": None}

    except Exception as e:
        logger.error(f"[{media_id}] Processing failed: {e}")
        db.update_media_status(media_id, "failed")
        return {"success": False, "detections": [], "error": str(e)}


def process_batch(
    media_records: list[dict], model_type: str = MODEL_YOLOV11
) -> list[dict]:
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
            model_type=model_type,
        )
        result["media_id"] = record["id"]
        results.append(result)
    return results
