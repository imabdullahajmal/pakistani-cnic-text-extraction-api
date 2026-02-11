import logging
import os
import numpy as np

# Disable oneDNN/MKLDNN to avoid compatibility issues
os.environ['FLAGS_use_mkldnn'] = '0'

from paddleocr import PaddleOCR

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from image regions using PaddleOCR."""

    def __init__(self):
        self._ocr: PaddleOCR | None = None

    def load_model(self) -> None:
        """Initialize the PaddleOCR engine."""
        try:
            # PaddleOCR 2.7.x uses use_gpu parameter
            # Check if CUDA is available via PaddlePaddle
            try:
                import paddle
                use_gpu = paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
            except Exception:
                use_gpu = False
            
            self._ocr = PaddleOCR(
                use_angle_cls=settings.OCR_USE_ANGLE_CLS,
                lang=settings.OCR_LANG,
                use_gpu=use_gpu,
                enable_mkldnn=False,
                show_log=False,
            )
            logger.info(f"PaddleOCR initialized successfully (GPU: {use_gpu})")
        except Exception as e:
            logger.error(f"Failed to load PaddleOCR: {e}")
            raise

    @property
    def is_loaded(self) -> bool:
        return self._ocr is not None

    def extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from a single image region.

        Args:
            image: BGR image as numpy array.

        Returns:
            Extracted text string.
        """
        if self._ocr is None:
            logger.error("OCR service called but not loaded")
            raise RuntimeError("OCR not loaded. Call load_model() first.")

        try:
            result = self._ocr.ocr(image, cls=True)
            logger.info(f"Raw OCR result type: {type(result)}, length: {len(result) if result else 0}")
            if result:
                logger.info(f"First element type: {type(result[0])}, value: {result[0]}")

            if result and result[0]:
                extracted = " ".join([line[1][0] for line in result[0]])
                logger.info(f"Extracted text from region: '{extracted}'")
                return extracted
            return ""
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise RuntimeError(f"OCR extraction failed: {str(e)}")

    def extract_texts_batch(self, images: list[np.ndarray]) -> list[str]:
        """
        Extract text from multiple image regions.

        Args:
            images: List of BGR images as numpy arrays.

        Returns:
            List of extracted text strings.
        """
        texts: list[str] = []
        for img in images:
            text = self.extract_text(img)
            texts.append(text if text else "No text detected")
        return texts


# Singleton instance
ocr_service = OCRService()
