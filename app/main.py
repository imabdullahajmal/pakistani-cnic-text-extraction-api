import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.extraction import router as extraction_router
from app.services.detector import detector
from app.services.ocr import ocr_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup, cleanup on shutdown."""
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"   CUDA version: {torch.version.cuda}")
        else:
            logger.warning("⚠ No GPU detected, running on CPU")
    except Exception as e:
        logger.warning(f"Could not check GPU status: {e}")
    
    logger.info("Loading YOLO detection model...")
    detector.load_model()
    logger.info("YOLO model loaded successfully.")

    logger.info("Loading PaddleOCR engine...")
    ocr_service.load_model()
    logger.info("PaddleOCR engine loaded successfully.")

    yield

    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "REST API for extracting structured text data from Pakistani CNIC "
        "(Computerized National Identity Card) images using YOLO object detection "
        "and PaddleOCR."
    ),
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Do not allow credentials with a wildcard origin (browsers will block this).
    # If you need credentialed requests, set `allow_origins` to an explicit list.
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=600,
)

# Register routes
app.include_router(extraction_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/ui", tags=["UI"])  # simple single-file UI to interact with the API
async def web_ui():
    """Serve the simple web UI (web_ui.html) placed at project root."""
    ui_path = settings.BASE_DIR / "web_ui.html"
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="UI not found. Create web_ui.html in project root.")
    return FileResponse(ui_path)
