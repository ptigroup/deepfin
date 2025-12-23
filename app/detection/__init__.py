"""Table detection module for PDF documents."""

from app.detection.models import DetectionResult, Document
from app.detection.routes import router

__all__ = ["Document", "DetectionResult", "router"]
