"""Test API response serialization."""
import sys
sys.path.insert(0, 'd:/Work/AI/cnic_text_extraction')
import json

from app.utils.parser import parse_cnic_fields
from app.models.schemas import ExtractionResponse, DetectionInfo

# Sample data
raw_texts = [
    "Country of Stay Saudi Arabia",
    "Identity Number Date of Birth 16202-0883647-3 24.08.1972 Date of Expiry Date of lssue 22.01.2021 22.01.2014",
    "Gender M",
    "Name Jamil Ahmad",
    "Fathet Name Khali Or Rahman",
]

cnic_data = parse_cnic_fields(raw_texts)

response = ExtractionResponse(
    success=True,
    message="Test",
    data=cnic_data,
    raw_texts=raw_texts,
    detection_info=DetectionInfo(
        total_regions_detected=5,
        detection_threshold=0.15
    )
)

# Test JSON serialization
json_str = response.model_dump_json(indent=2)
print("API Response JSON:")
print(json_str)

# Parse back
parsed = json.loads(json_str)
print("\n" + "=" * 60)
print("Checking data fields in JSON:")
print("=" * 60)
print(f"data.date_of_birth: {parsed['data']['date_of_birth']}")
print(f"data.date_of_issue: {parsed['data']['date_of_issue']}")
print(f"data.date_of_expiry: {parsed['data']['date_of_expiry']}")
print(f"data.name: {parsed['data']['name']}")
print(f"data.father_name: {parsed['data']['father_name']}")
