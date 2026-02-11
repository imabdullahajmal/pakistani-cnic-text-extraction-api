# CNIC Text Extraction API - Implementation Guide

## What Was Implemented

### 1. **Robust CNIC Parser** (`app/utils/parser_v2.py`)
- Handles OCR errors and typos (e.g., "Gende" → "Gender", "Fathet" → "Father")
- Prioritizes labeled fields over standalone text
- Extracts 8 key fields:
  - `name` (person's name from "Name" label)
  - `father_name` (from "Father Name" label)
  - `gender` (Male/Female)
  - `country_of_stay` (from "Country of Stay")
  - `identity_number` (XXXXX-XXXXXXX-X format)
  - `date_of_birth` (DD/MM/YYYY)
  - `date_of_issue` (DD/MM/YYYY)
  - `date_of_expiry` (DD/MM/YYYY)
- Intelligent multi-field line parsing
- Filters out header noise and "No text detected" entries
- Fallback to standalone name detection (correct order: father first, then person)

### 2. **Clean JSON API Endpoint** (`/api/v1/extract-json`)
- Returns only structured CNIC fields (no raw text clutter)
- Response format:
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

### 3. **Improved Web UI** (`web_ui.html`)
- Displays structured fields as formatted Markdown
- Shows JSON output for debugging
- Clean, professional presentation
- Download extracted data as Markdown file

### 4. **Fixed CORS Configuration**
- Removed credential conflicts
- Supports browser-based file uploads

## How to Run

### Start the Server
```bash
venv\Scripts\python.exe run.py
```

The server will start on http://localhost:8000

### Access the Web UI
Open your browser and go to:
```
http://localhost:8000/ui
```

### API Endpoints

#### 1. Extract CNIC (Clean JSON)
```bash
POST /api/v1/extract-json
Content-Type: multipart/form-data

# Returns structured JSON with 7 key fields
```

#### 2. Extract CNIC (Full Details)
```bash
POST /api/v1/extract
Content-Type: multipart/form-data

# Returns full extraction with raw texts and metadata
```

#### 3. Health Check
```bash
GET /api/v1/health

# Returns API status and model loading info
```

## Testing with Your Image

1. **Start the server**:
   ```bash
   venv\Scripts\python.exe run.py
   ```

2. **Open the Web UI**: http://localhost:8000/ui

3. **Upload your CNIC image** and click "Extract"

4. **Expected Result** (based on your sample):
   ```
   Name: Saif Ullah
   Father Name: Ghulam Hussain
   Gender: Male
   Country of Stay: Pakistan
   Identity Number: 38403-9346396-1
   Date of Birth: 10/11/1987
   Date of Issue: 12/06/2013
   Date of Expiry: 12/06/2020
   ```

## API Usage Example (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/extract-json" \
  -F "file=@path/to/cnic_image.jpg"
```

## API Usage Example (Python)

```python
import requests

url = "http://localhost:8000/api/v1/extract-json"
files = {"file": open("cnic_image.jpg", "rb")}

response = requests.post(url, files=files)
data = response.json()

if data["success"]:
    cnic = data["data"]
    print(f"Name: {cnic['name']}")
    print(f"Father: {cnic['father_name']}")
    print(f"ID: {cnic['identity_number']}")
else:
    print(f"Error: {data['message']}")
```

## Key Features

### Error Handling
- Handles OCR typos (Gende → Gender)
- Normalizes date formats
- Cleans unwanted text
- Filters header/footer noise

### Multi-Field Line Support
Correctly parses lines like:
```
Identity Number Date of Birth 38403-9346396-1 10.11.1987
Date of Issue Date of Expiry 12.06.2013 12.06.2020
```

### Standalone Text Detection
Extracts names even when labels are missing or misread

### Date Normalization
Converts all date formats to DD/MM/YYYY:
- `10.11.1987` → `10/11/1987`
- `12-06-2013` → `12/06/2013`

## GPU Configuration

Current setup:
- **YOLO (Detection)**: Runs on GPU (RTX 4060)
- **PaddleOCR**: Runs on CPU (stable, compatible)

Your system:
- GPU: RTX 4060
- CUDA: 12.4 (via PyTorch 2.5.1+cu124)

## Package Versions (Tested & Working)

```
paddlepaddle==2.6.2
paddleocr==2.7.3
numpy<2.0 (1.26.4)
ultralytics>=8.0.0
opencv-python>=4.8.0
torch==2.5.1+cu124
```

## Next Steps

1. **Test with more CNIC images** to tune regex patterns
2. **Add confidence scores** for each field
3. **Implement field validation** (e.g., CNIC format check)
4. **Add support for Urdu text** if needed

## Troubleshooting

### Models not loading?
```bash
# Check GPU availability
venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
```

### CORS errors?
- Make sure to access UI via `http://localhost:8000/ui` (not file://)
- Check browser console for specific errors

### Poor extraction quality?
- Adjust detection threshold: `POST /api/v1/extract-json?threshold=0.2`
- Ensure image is clear and well-lit
- Image should be front side of CNIC only
