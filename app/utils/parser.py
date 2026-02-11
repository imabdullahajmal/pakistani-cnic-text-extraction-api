import logging
import re

from app.models.schemas import CNICData

logger = logging.getLogger(__name__)


def parse_cnic_fields(raw_texts: list[str]) -> CNICData:
    """
    Parse raw OCR texts from detected CNIC regions into structured fields.

    Uses pattern matching and keyword detection to map extracted text
    to the appropriate CNIC fields.

    Args:
        raw_texts: List of raw text strings from OCR.

    Returns:
        CNICData with populated fields.
    """
    logger.info(f"Parsing {len(raw_texts)} OCR text regions")
    logger.debug(f"Raw texts: {raw_texts}")
    
    data: dict[str, str | None] = {
        "name": None,
        "father_name": None,
        "gender": None,
        "country_of_stay": None,
        "identity_number": None,
        "date_of_birth": None,
        "date_of_issue": None,
        "date_of_expiry": None,
    }

    # Combine all texts for full-text analysis as well
    combined = " ".join(raw_texts)
    
    # Track standalone dates and names for context-based matching
    standalone_dates = []
    standalone_names = []

    for text in raw_texts:
        text_stripped = text.strip()
        text_lower = text_stripped.lower()
        
        # Normalize common OCR typos
        text_lower = text_lower.replace("lssue", "issue").replace("fathet", "father")
        text_stripped = text_stripped.replace("lssue", "issue").replace("Fathet", "Father")

        # --- Identity Number (CNIC format: XXXXX-XXXXXXX-X) ---
        cnic_match = re.search(r"\d{5}-\d{7}-\d", text_stripped)
        if cnic_match:
            data["identity_number"] = cnic_match.group()

        # Also check for 13-digit number without dashes
        if not data["identity_number"]:
            cnic_nodash = re.search(r"\b\d{13}\b", text_stripped)
            if cnic_nodash:
                digits = cnic_nodash.group()
                data["identity_number"] = f"{digits[:5]}-{digits[5:12]}-{digits[12]}"

        # --- Gender ---
        if re.search(r"\bgender\b", text_lower):
            gender_match = re.search(r"\b([MF])\b", text_stripped)
            if gender_match:
                data["gender"] = "Male" if gender_match.group(1) == "M" else "Female"
            elif "female" in text_lower:
                data["gender"] = "Female"
            elif "male" in text_lower:
                data["gender"] = "Male"

        # --- Country of Stay ---
        if "country of stay" in text_lower and not data["country_of_stay"]:
            value = re.sub(r"(?i)country\s+of\s+stay\s*:?\s*", "", text_stripped).strip()
            if value and not _is_label_only(value):
                data["country_of_stay"] = value.title()

        # --- Extract dates with context ---
        # Check if this is a multi-field line first (multiple dates/keywords)
        has_multiple_dates = len(re.findall(r"\d{2}[./-]\d{2}[./-]\d{4}", text_stripped)) >= 2
        has_multiple_keywords = text_lower.count("date") >= 2 or sum([
            "birth" in text_lower,
            "issue" in text_lower,
            "expiry" in text_lower
        ]) >= 2
        
        # Special handling for multi-field lines (all dates in one OCR line)
        # Example: "Identity Number Date of Birth 16202-0883647-3 24.08.1972 Date of Expiry Date of Issue 22.01.2021 22.01.2014"
        if has_multiple_dates and has_multiple_keywords:
            # Extract all dates with their positions
            all_dates_raw = re.findall(r"\d{2}[./-]\d{2}[./-]\d{4}", text_stripped)
            all_dates = [d.replace("-", "/").replace(".", "/") for d in all_dates_raw]
            
            # Find positions of each date in the original text
            date_positions = []
            for date_raw in all_dates_raw:
                pos = text_stripped.find(date_raw)
                date_positions.append((pos, date_raw.replace("-", "/").replace(".", "/")))
            
            # Find keyword positions
            keywords = [
                ("birth", "date_of_birth"),
                ("expiry", "date_of_expiry"),
                ("issue", "date_of_issue")
            ]
            
            keyword_positions = []
            for keyword, field in keywords:
                if keyword in text_lower and not data[field]:
                    pos = text_lower.find(keyword)
                    keyword_positions.append((pos, field))
            
            # Sort keywords by position
            keyword_positions.sort(key=lambda x: x[0])
            
            # Match each keyword with the nearest following date
            used_dates = set()
            for kw_pos, field in keyword_positions:
                # Find the first date after this keyword that hasn't been used
                for date_pos, date_val in date_positions:
                    if date_pos > kw_pos and date_val not in used_dates:
                        data[field] = date_val
                        used_dates.add(date_val)
                        logger.info(f"Extracted {field} from multi-field line: {date_val}")
                        break
        
        # Handle single-field date lines (one keyword, one date)
        else:
            if "birth" in text_lower and not data["date_of_birth"]:
                birth_match = re.search(r"(?:date\s+of\s+)?birth[^\d]*(\d{2}[./-]\d{2}[./-]\d{4})", text_stripped, re.IGNORECASE)
                if birth_match:
                    data["date_of_birth"] = birth_match.group(1).replace("-", "/").replace(".", "/")
                    logger.info(f"Extracted date_of_birth: {data['date_of_birth']}")
            
            if "issue" in text_lower and not data["date_of_issue"]:
                issue_match = re.search(r"(?:date\s+of\s+)?issue[^\d]*(\d{2}[./-]\d{2}[./-]\d{4})", text_stripped, re.IGNORECASE)
                if issue_match:
                    data["date_of_issue"] = issue_match.group(1).replace("-", "/").replace(".", "/")
                    logger.info(f"Extracted date_of_issue: {data['date_of_issue']}")
            
            if "expiry" in text_lower and not data["date_of_expiry"]:
                expiry_match = re.search(r"(?:date\s+of\s+)?expiry[^\d]*(\d{2}[./-]\d{2}[./-]\d{4})", text_stripped, re.IGNORECASE)
                if expiry_match:
                    data["date_of_expiry"] = expiry_match.group(1).replace("-", "/").replace(".", "/")
                    logger.info(f"Extracted date_of_expiry: {data['date_of_expiry']}")
        
        # Collect standalone dates for later context matching
        if re.match(r"^\d{2}[./-]\d{2}[./-]\d{4}$", text_stripped.strip()):
            normalized_date = text_stripped.strip().replace("-", "/").replace(".", "/")
            standalone_dates.append(normalized_date)

        # --- Father's Name ---
        if "father" in text_lower and not data["father_name"]:
            value = re.sub(r"(?i)father'?s?\s+name\s*:?\s*", "", text_stripped).strip()
            # Clean up OCR artifacts (single letters that should be part of names)
            value = re.sub(r"\s+Or\s+", " ", value, flags=re.IGNORECASE)  # "Khali Or Rahman" -> "Khali Rahman"
            if value and not _is_label_only(value) and len(value) > 2:
                data["father_name"] = value.title()

        # --- Name (comes after "Name" label, avoid header text) ---
        if (re.search(r"(?i)^name\b", text_stripped) or re.search(r"(?i)name\s*:", text_stripped)) and not data["name"]:
            value = re.sub(r"(?i)^name\s*:?\s*", "", text_stripped).strip()
            if value and not _is_label_only(value) and len(value) > 2:
                data["name"] = value.title()
        
        # Collect potential name values (alphabetic text, 2+ words, reasonable length)
        if (re.match(r"^[A-Za-z ]{5,50}$", text_stripped) and 
            len(text_stripped.split()) >= 2 and
            not _is_label_only(text_stripped)):
            standalone_names.append(text_stripped)

    # Second pass: try to extract from combined text for any missed fields
    _extract_missing_from_combined(data, combined)
    
    # Third pass: intelligent matching of standalone values using context
    _match_standalone_values(data, raw_texts, standalone_dates, standalone_names)
    
    logger.info(f"Parsed data: {data}")
    return CNICData(**data)


def _is_label_only(text: str) -> bool:
    """Check if text is just a label keyword with no actual value."""
    labels = {
        "pakistan", "national", "identity", "card", "islamic",
        "republic", "holder", "signature", "holder's signature",
        "name", "father", "fathers", "gender", "country", "date",
        "birth", "issue", "expiry", "stay", "of", "the",
    }
    return text.strip().lower() in labels


def _extract_missing_from_combined(data: dict, combined: str) -> None:
    """Try to fill missing fields from the combined text using regex."""

    # Identity number
    if not data["identity_number"]:
        match = re.search(r"\d{5}-\d{7}-\d", combined)
        if match:
            data["identity_number"] = match.group()

    # Normalize OCR typos in combined text
    combined = combined.replace("lssue", "issue").replace("Fathet", "Father").replace("fathet", "father")
    
    # Dates - more flexible patterns with typo tolerance
    if not data["date_of_birth"]:
        match = re.search(
            r"(?i)(?:date\s+of\s+)?birth[^\d]*(\d{2}[./-]\d{2}[./-]\d{4})", combined
        )
        if match:
            data["date_of_birth"] = match.group(1).replace("-", "/").replace(".", "/")

    if not data["date_of_issue"]:
        match = re.search(
            r"(?i)(?:date\s+of\s+)?issue[^\d]*(\d{2}[./-]\d{2}[./-]\d{4})", combined
        )
        if match:
            data["date_of_issue"] = match.group(1).replace("-", "/").replace(".", "/")

    if not data["date_of_expiry"]:
        match = re.search(
            r"(?i)(?:date\s+of\s+)?expiry[^\d]*(\d{2}[./-]\d{2}[./-]\d{4})", combined
        )
        if match:
            data["date_of_expiry"] = match.group(1).replace("-", "/").replace(".", "/")

    # Name - use finditer to check context and avoid variable-width look-behind
    if not data["name"]:
        for match in re.finditer(r"(?i)\bname\s+([A-Za-z ]+)", combined):
            # Check if this is not part of "father's name"
            start = match.start()
            prefix = combined[max(0, start - 15):start].lower()
            if "father" not in prefix:
                value = match.group(1).strip()
                if not _is_label_only(value):
                    data["name"] = value.title()
                    break

    # Father's name - more flexible
    if not data["father_name"]:
        match = re.search(r"(?i)father'?s?\s+name\s*:?\s+([A-Za-z ]{3,50})", combined)
        if match:
            value = match.group(1).strip()
            # Clean up potential trailing noise
            value = re.split(r"\s+(?:gender|country|date|identity|holder)", value, flags=re.IGNORECASE)[0]
            # Clean up OCR artifacts
            value = re.sub(r"\s+Or\s+", " ", value, flags=re.IGNORECASE)
            if not _is_label_only(value) and len(value) > 2:
                data["father_name"] = value.title()

    # Gender
    if not data["gender"]:
        match = re.search(r"(?i)gender\s+([MF])\b", combined)
        if match:
            data["gender"] = "Male" if match.group(1).upper() == "M" else "Female"


def _match_standalone_values(
    data: dict, 
    raw_texts: list[str], 
    standalone_dates: list[str], 
    standalone_names: list[str]
) -> None:
    """
    Intelligently match standalone dates and names to fields based on context.
    
    This handles cases where OCR splits labels and values into separate regions.
    """
    # Match dates to fields based on nearby label text
    for i, text in enumerate(raw_texts):
        text_lower = text.lower()
        
        # Look for date labels and check next few regions for standalone dates
        if "birth" in text_lower and not data["date_of_birth"]:
            for j in range(max(0, i-2), min(len(raw_texts), i+3)):
                if raw_texts[j].strip() in standalone_dates:
                    data["date_of_birth"] = raw_texts[j].strip()
                    logger.info(f"Matched date of birth from context: {data['date_of_birth']}")
                    break
        
        if "issue" in text_lower and not data["date_of_issue"]:
            for j in range(max(0, i-2), min(len(raw_texts), i+3)):
                if raw_texts[j].strip() in standalone_dates:
                    data["date_of_issue"] = raw_texts[j].strip()
                    logger.info(f"Matched date of issue from context: {data['date_of_issue']}")
                    break
        
        if "expiry" in text_lower and not data["date_of_expiry"]:
            for j in range(max(0, i-2), min(len(raw_texts), i+3)):
                if raw_texts[j].strip() in standalone_dates:
                    data["date_of_expiry"] = raw_texts[j].strip()
                    logger.info(f"Matched date of expiry from context: {data['date_of_expiry']}")
                    break
        
        # Match names based on context
        if "father" in text_lower and not data["father_name"]:
            for j in range(max(0, i-2), min(len(raw_texts), i+3)):
                if raw_texts[j].strip().title() in [n.title() for n in standalone_names]:
                    data["father_name"] = raw_texts[j].strip().title()
                    logger.info(f"Matched father's name from context: {data['father_name']}")
                    break
        
        # Match person's name - should be near beginning, not near "father"
        if (re.search(r"(?i)^name\b", text_lower) or "name" == text_lower.strip()) and not data["name"]:
            # Avoid matching near father's name label
            context_lower = " ".join(raw_texts[max(0, i-2):min(len(raw_texts), i+3)]).lower()
            if "father" not in context_lower:
                for j in range(max(0, i-2), min(len(raw_texts), i+3)):
                    if raw_texts[j].strip().title() in [n.title() for n in standalone_names]:
                        data["name"] = raw_texts[j].strip().title()
                        logger.info(f"Matched name from context: {data['name']}")
                        break
