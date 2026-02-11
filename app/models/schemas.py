from pydantic import BaseModel
from typing import Optional


class CNICData(BaseModel):
    """Structured CNIC extracted data."""
    name: Optional[str] = None
    father_name: Optional[str] = None
    gender: Optional[str] = None
    country_of_stay: Optional[str] = None
    identity_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    date_of_issue: Optional[str] = None
    date_of_expiry: Optional[str] = None


class CNICDataClean(BaseModel):
    """Clean CNIC data with essential fields."""
    name: Optional[str] = None
    father_name: Optional[str] = None
    gender: Optional[str] = None
    country_of_stay: Optional[str] = None
    identity_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    date_of_issue: Optional[str] = None
    date_of_expiry: Optional[str] = None


class DetectionInfo(BaseModel):
    """Detection metadata."""
    total_regions_detected: int
    detection_threshold: float


class ExtractionResponse(BaseModel):
    """Full API response for CNIC extraction."""
    success: bool
    message: str
    data: Optional[CNICData] = None
    raw_texts: list[str] = []
    detection_info: Optional[DetectionInfo] = None


class CleanExtractionResponse(BaseModel):
    """Clean JSON response with only essential CNIC fields."""
    success: bool
    message: str
    data: Optional[CNICDataClean] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    app_name: str
    version: str
    model_loaded: bool
    ocr_loaded: bool
