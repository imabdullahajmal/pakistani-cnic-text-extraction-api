"""Test parser with sample OCR data."""
import sys
import logging
sys.path.insert(0, 'd:/Work/AI/cnic_text_extraction')

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from app.utils.parser import parse_cnic_fields

# Sample data from user's report
raw_texts = [
    "Country of Stay Saudi Arabia",
    "Identity Number Date of Birth 16202-0883647-3 24.08.1972 Date of Expiry Date of lssue 22.01.2021 22.01.2014",
    "Gender M",
    "Name Jamil Ahmad",
    "No text detected",
    "No text detected",
    "Fathet Name Khali Or Rahman",
    "PAKISTAN National Identity Card LAC REPUELC OE AKN",
    "KISTAN National Identity Card"
]

print("Testing parser with sample OCR data...")
print("=" * 60)
print("\nRaw OCR texts:")
for i, text in enumerate(raw_texts, 1):
    print(f"[{i}] {text}")

print("\n" + "=" * 60)
print("Parsing results:")
print("=" * 60)

result = parse_cnic_fields(raw_texts)
print(f"\nName: {result.name}")
print(f"Father's Name: {result.father_name}")
print(f"Gender: {result.gender}")
print(f"Country of Stay: {result.country_of_stay}")
print(f"Identity Number: {result.identity_number}")
print(f"Date of Birth: {result.date_of_birth}")
print(f"Date of Issue: {result.date_of_issue}")
print(f"Date of Expiry: {result.date_of_expiry}")

print("\n" + "=" * 60)
print("\nExpected ALL FIELDS PRESENT:")
print("  Name: Jamil Ahmad")
print("  Father's Name: Khali Rahman")
print("  Gender: Male")
print("  Country of Stay: Saudi Arabia")
print("  Identity Number: 16202-0883647-3")
print("  Date of Birth: 24/08/1972")
print("  Date of Issue: 22/01/2014")
print("  Date of Expiry: 22/01/2021")
print("=" * 60)
