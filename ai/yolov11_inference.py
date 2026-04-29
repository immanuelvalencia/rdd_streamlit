"""
YOLOv11 Inference Engine for Road Damage Detection
====================================================
Place your trained model at:
  models/yolov11/weights/best.pt

Optionally update the class labels at:
  models/yolov11/labels/classes.txt

Dependencies:
  pip install ultralytics opencv-python-headless pillow requests
"""

import io
import os
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR     = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = BASE_DIR / "models" / "yolov11" / "weights" / "best.pt"
LABELS_PATH  = BASE_DIR / "models" / "yolov11" / "labels" / "classes.txt"

# ── Model loader (singleton) ──────────────────────────────────────────────────

_model = None

def load_model(weights_path: Path = WEIGHTS_PATH):
    """
    Loads the YOLO11 model from the given .pt path.
    Caches the model in memory so it's only loaded once per process.
    """
    global _model
    if _model is None:
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics is not installed. Run: pip install ultralytics"
            )

        if not weights_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at: {weights_path}\n"
                "Place your trained best.pt file in models/yolov11/weights/"
            )

        logger.info(f"Loading YOLO11 model from {weights_path}")
        _model = YOLO(str(weights_path))
        logger.info(f"Model loaded. Classes: {_model.names}")

    return _model


def get_class_names(model) -> dict:
    """
    Returns class names from the model. Falls back to classes.txt if needed.
    Model-embedded names always take priority.
    """
    if hasattr(model, 'names') and model.names:
        return model.names  # dict: {0: 'pothole', 1: 'crack', ...}

    # Fallback: read from classes.txt
    if LABELS_PATH.exists():
        with open(LABELS_PATH, 'r') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        return {i: name for i, name in enumerate(lines)}

    return {}

# ── Inference ─────────────────────────────────────────────────────────────────

def run_inference(
    image_bytes: bytes,
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    imgsz: int = 640,
) -> tuple[list[dict], bytes]:
    """
    Runs YOLO11 inference on the given image bytes.

    Args:
        image_bytes:    Raw image bytes (JPEG, PNG, etc.)
        conf_threshold: Minimum confidence to include a detection (0–1)
        iou_threshold:  IOU threshold for NMS
        imgsz:          Inference image size

    Returns:
        detections:     List of dicts with keys:
                          - damage_type (str)
                          - confidence  (float, 0–1)
                          - bbox        ([x1, y1, x2, y2] in pixels)
        annotated_bytes: JPEG bytes of the annotated image with bounding boxes
    """
    model = load_model()

    # Convert bytes → PIL Image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Run inference
    results = model.predict(
        source=image,
        conf=conf_threshold,
        iou=iou_threshold,
        imgsz=imgsz,
        verbose=False,
    )

    class_names = get_class_names(model)
    detections = []

    result = results[0]  # single image
    if result.boxes is not None:
        for box in result.boxes:
            class_id   = int(box.cls[0].item())
            confidence = round(float(box.conf[0].item()), 4)
            bbox       = [round(v, 1) for v in box.xyxy[0].tolist()]
            damage_type = class_names.get(class_id, f"class_{class_id}")

            detections.append({
                "damage_type": damage_type,
                "confidence":  confidence,
                "bbox":        bbox,       # [x1, y1, x2, y2]
            })

    # Generate annotated image (BGR numpy array)
    annotated_np = result.plot()  # draws boxes, labels, confidence scores

    # Encode to JPEG bytes
    success, buffer = cv2.imencode(".jpg", annotated_np, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        # Fallback: use PIL to save
        annotated_rgb = cv2.cvtColor(annotated_np, cv2.COLOR_BGR2RGB)
        pil_out = Image.fromarray(annotated_rgb)
        buf = io.BytesIO()
        pil_out.save(buf, format="JPEG", quality=90)
        annotated_bytes = buf.getvalue()
    else:
        annotated_bytes = buffer.tobytes()

    logger.info(f"Inference complete: {len(detections)} detection(s) found")
    return detections, annotated_bytes


def is_model_available() -> bool:
    """Returns True if the model weights file exists."""
    return WEIGHTS_PATH.exists()
