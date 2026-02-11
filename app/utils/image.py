import cv2
import numpy as np
from fastapi import UploadFile

from app.config import settings


async def read_image_from_upload(file: UploadFile) -> np.ndarray:
    """
    Read an uploaded file and convert it to an OpenCV image (BGR).

    Args:
        file: FastAPI UploadFile object.

    Returns:
        Image as numpy array in BGR format.

    Raises:
        ValueError: If file is too large or not a valid image.
    """
    contents = await file.read()

    # Check file size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise ValueError(
            f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit."
        )

    # Decode image
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Could not decode image. Ensure it is a valid image file.")

    return image


def validate_image_file(file: UploadFile) -> None:
    """
    Validate the uploaded file is an acceptable image type.

    Args:
        file: FastAPI UploadFile object.

    Raises:
        ValueError: If the file type is not supported.
    """
    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/bmp",
        "image/webp",
    }

    if file.content_type and file.content_type not in allowed_types:
        raise ValueError(
            f"Unsupported file type: {file.content_type}. "
            f"Allowed: {', '.join(allowed_types)}"
        )
