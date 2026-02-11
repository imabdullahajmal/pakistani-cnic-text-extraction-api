# CNIC Text Extraction API

This repository provides a small REST API and a single-file web UI to extract structured fields from Pakistani CNIC (Computerized National Identity Card) images.

Features
- YOLO-based detection for text regions (ultralytics)
- OCR using PaddleOCR
- Robust parser that returns clean, structured JSON with CNIC fields

Important behavior
- The clean JSON endpoint (`/api/v1/extract-json`) requires all essential fields to be present in the image. If any required field is missing or clearly OCR-incorrect, the API will return an error requesting a clearer image. This strict validation prevents downstream data errors.

This README documents how to set up the project, run it locally, and troubleshoot common issues you might encounter on Windows.

## Quick start (Windows)

Prerequisites
- Python 3.10 (the project was developed against Python 3.10)
- Git (optional)
- A machine with or without an NVIDIA GPU. YOLO uses your system's PyTorch installation for GPU acceleration. PaddleOCR can run on CPU or GPU; GPU use requires a matching `paddlepaddle-gpu` wheel for your CUDA version.

1) Create and activate a virtual environment

PowerShell (recommended):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Command Prompt:

```bat
python -m venv venv
venv\Scripts\activate
```

2) Install Python dependencies

```powershell
pip install -r requirements.txt
```

Notes about PaddlePaddle (GPU)
- If you want PaddleOCR to use GPU, install a `paddlepaddle-gpu` wheel that matches your CUDA/cuDNN versions. The correct wheel must be chosen from the PaddlePaddle download instructions; installing the wrong wheel commonly produces missing `cudnn` DLL errors on Windows. If you do not want to manage GPU dependencies, keep `paddlepaddle` (CPU) installed and PaddleOCR will run on CPU.

3) Start the server

```powershell
python run.py
```

4) Use the web UI

Open the browser and visit:

```
http://localhost:8000/ui
```

You can upload a front-side CNIC image and click Extract. The web UI calls the `/api/v1/extract-json` endpoint and shows structured fields.

## API

Endpoints (prefix `/api/v1`):
- `POST /extract` — Full response including `raw_texts` and parsing metadata.
- `POST /raw-text` — Returns only raw OCR texts.
- `POST /extract-json` — Returns a clean JSON object with CNIC fields (required fields enforced).
- `GET /health` — Health & model load status.

`/extract-json` response example

```json
{
	"success": true,
	"message": "CNIC data extracted successfully.",
	"data": {
		"name": "Saif Ullah",
		"father_name": "Ghulam Hussain",
		"gender": "Male",
		"country_of_stay": "Pakistan",
		"identity_number": "38403-9346396-1",
		"date_of_birth": "10/11/1987",
		"date_of_issue": "12/06/2013",
		"date_of_expiry": "12/06/2020"
	}
}
```

If any required field is missing or clearly invalid, the endpoint responds with `success: false` and an explanatory `message` telling the caller the image is unclear.

## Troubleshooting

- PaddlePaddle GPU errors (missing cudnn DLL): choose the correct `paddlepaddle-gpu` wheel for your CUDA/cuDNN, or install the CPU `paddlepaddle` and run PaddleOCR on CPU.
- Numpy/OpenCV ABI errors: use the provided `requirements.txt` and a fresh virtual environment. The chosen version set resolves common ABI mismatches between `numpy`, `opencv-python`, and other native wheels.
- CORS: access the UI via `http://localhost:8000/ui`. Do not open the HTML file via `file://`.

## Implementation notes

- YOLO detection runs on GPU when available (PyTorch must be installed with CUDA). PaddleOCR runs on CPU by default (GPU optional as described above).
- The parser is intentionally strict: it prioritizes labeled fields (e.g., lines containing "Name" or "Father") and falls back to standalone heuristics only if labeled values are missing. The API will reject images that do not provide all required fields to avoid returning incorrect data.

For more detailed developer notes and troubleshooting steps, see `IMPLEMENTATION_GUIDE.md`.

---

If you want I can also add a small `CONTRIBUTING.md` with a testing checklist.