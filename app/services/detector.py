import cv2
import logging
import numpy as np
from ultralytics import YOLO

from app.config import MODEL_PATH, settings

logger = logging.getLogger(__name__)


class DetectionService:
    """Service for detecting text regions on CNIC images using YOLO."""

    def __init__(self):
        self._model: YOLO | None = None
        self._device: str = "cuda" if self._is_cuda_available() else "cpu"

    @staticmethod
    def _is_cuda_available() -> bool:
        """Check if CUDA is available for PyTorch."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def load_model(self) -> None:
        """Load the YOLO model into memory."""
        self._model = YOLO(str(MODEL_PATH))
        # Force model to use GPU if available
        self._model.to(self._device)
        logger.info(f"YOLO model loaded (device: {self._device})")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def detect_and_crop(
        self,
        image: np.ndarray,
        threshold: float | None = None,
    ) -> list[np.ndarray]:
        """
        Run YOLO detection on an image and return cropped text regions.

        Args:
            image: BGR image as numpy array.
            threshold: Confidence threshold (uses config default if None).

        Returns:
            List of cropped image regions (numpy arrays).
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        threshold = threshold or settings.DETECTION_THRESHOLD
        results = self._model(image)[0]

        cropped_images: list[np.ndarray] = []
        for x1, y1, x2, y2, score, class_id in results.boxes.data.tolist():
            if score > threshold:
                cropped = image[int(y1):int(y2), int(x1):int(x2)]
                cropped_images.append(cropped)
        
        logger.info(f"Detected {len(cropped_images)} text regions with threshold {threshold}")
        return cropped_images


# Singleton instance
detector = DetectionService()
