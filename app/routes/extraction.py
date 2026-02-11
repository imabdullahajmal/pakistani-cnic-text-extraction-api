import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    CNICData,
    CNICDataClean,
    DetectionInfo,
    ExtractionResponse,
    CleanExtractionResponse,
    HealthResponse,
)
from app.services.detector import detector
from app.services.ocr import ocr_service
from app.utils.image import read_image_from_upload, validate_image_file
from app.utils.parser import parse_cnic_fields
from app.utils.parser_v2 import cnic_parser
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["CNIC Extraction"])


@router.post("/extract", response_model=ExtractionResponse)
async def extract_cnic(
    file: UploadFile = File(..., description="CNIC image file (JPEG, PNG, BMP, WEBP)"),
    threshold: float | None = None,
    parse: bool = True,
):
    """
    Extract text from a CNIC image.

    Accepts an image upload, detects text regions using YOLO,
    runs OCR on each region, and returns structured CNIC data in JSON.
    """
    try:
        # Validate file type
        validate_image_file(file)

        # Read image
        image = await read_image_from_upload(file)

        # Detect text regions
        cropped_images = detector.detect_and_crop(image, threshold=threshold)

        if not cropped_images:
            return ExtractionResponse(
                success=False,
                message="No text regions detected in the image. "
                        "Ensure the image contains a clear CNIC.",
                detection_info=DetectionInfo(
                    total_regions_detected=0,
                    detection_threshold=threshold or settings.DETECTION_THRESHOLD,
                ),
            )

        # Run OCR on each cropped region
        raw_texts = ocr_service.extract_texts_batch(cropped_images)
        logger.info(f"Raw OCR texts: {raw_texts}")

        # Parse into structured fields (optional)
        if parse:
            cnic_data = parse_cnic_fields(raw_texts)
            logger.info(f"Parsed CNIC data: {cnic_data.model_dump()}")
        else:
            cnic_data = None

        return ExtractionResponse(
            success=True,
            message="CNIC data extracted successfully." if parse else "Raw OCR text extracted (parsing disabled).",
            data=cnic_data,
            raw_texts=raw_texts,
            detection_info=DetectionInfo(
                total_regions_detected=len(cropped_images),
                detection_threshold=threshold or settings.DETECTION_THRESHOLD,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post("/raw-text")
async def extract_raw_text(
    file: UploadFile = File(..., description="CNIC image file (JPEG, PNG, BMP, WEBP)"),
    threshold: float | None = None,
):
    """Extract and return only raw OCR text without parsing."""
    try:
        validate_image_file(file)
        image = await read_image_from_upload(file)
        cropped_images = detector.detect_and_crop(image, threshold=threshold)
        
        if not cropped_images:
            return {"success": False, "raw_texts": [], "message": "No text regions detected"}
        
        raw_texts = ocr_service.extract_texts_batch(cropped_images)
        
        return {
            "success": True,
            "raw_texts": raw_texts,
            "total_regions": len(cropped_images)
        }
    except Exception as e:
        logger.exception("Error extracting raw text")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-json", response_model=CleanExtractionResponse)
async def extract_cnic_json(
    file: UploadFile = File(..., description="CNIC image file (JPEG, PNG, BMP, WEBP)"),
    threshold: float | None = None,
):
    """
    Extract CNIC data and return clean JSON with only essential fields.
    
    This endpoint uses an improved parser that handles OCR errors and returns
    only the 7 key fields: name, father_name, gender, identity_number,
    date_of_birth, date_of_issue, date_of_expiry.
    """
    try:
        # Validate file type
        validate_image_file(file)

        # Read image
        image = await read_image_from_upload(file)

        # Detect text regions
        cropped_images = detector.detect_and_crop(image, threshold=threshold)

        if not cropped_images:
            return CleanExtractionResponse(
                success=False,
                message="No text regions detected. Ensure the image contains a clear CNIC.",
                data=None,
            )

        # Run OCR on each cropped region
        raw_texts = ocr_service.extract_texts_batch(cropped_images)
        logger.info(f"Raw OCR texts: {raw_texts}")

        # Parse with improved parser (returns data and optional error)
        parsed_data, validation_error = cnic_parser.parse(raw_texts)
        
        # If validation fails, return error
        if validation_error:
            return CleanExtractionResponse(
                success=False,
                message=validation_error,
                data=None,
            )
        
        cnic_data_clean = CNICDataClean(**parsed_data)
        
        logger.info(f"Parsed CNIC data: {parsed_data}")

        return CleanExtractionResponse(
            success=True,
            message="CNIC data extracted successfully.",
            data=cnic_data_clean,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during extraction")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of the API and model status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        model_loaded=detector.is_loaded,
        ocr_loaded=ocr_service.is_loaded,
    )
