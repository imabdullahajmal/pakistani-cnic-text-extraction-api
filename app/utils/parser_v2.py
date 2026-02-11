"""
Improved CNIC parser with robust error handling for OCR mistakes.
Extracts 8 key fields with validation: name, father_name, gender, country_of_stay,
identity_number, date_of_birth, date_of_issue, date_of_expiry.
"""
import logging
import re
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CNICParser:
    """Parse raw OCR texts into structured CNIC fields with error correction."""
    
    def __init__(self):
        # Common OCR typos and corrections
        self.typo_corrections = {
            "gende": "gender",
            "gendei": "gender",
            "gendet": "gender",
            "fathet": "father",
            "lssue": "issue",
            "birt": "birth",
            "expir": "expiry",
            "countryofstay": "country of stay",
            "country ofstay": "country of stay",
            "countryof stay": "country of stay",
        }
        
        # Words to ignore when cleaning extracted values
        self.ignore_words = {
            "pakistan", "national", "identity", "card", "islamic",
            "republic", "holder", "signature", "holders", "no", "text",
            "detected", "of", "the", "date", "name", "father", "gender",
            "country", "stay", "birth", "issue", "expiry", "number"
        }
        
        # Valid countries for CNIC
        self.valid_countries = {
            "pakistan", "afghanistan", "india", "iran", "china", "saudi arabia",
            "united arab emirates", "uae", "united kingdom", "uk", "united states",
            "usa", "canada", "australia", "turkey", "malaysia", "indonesia"
        }
    
    def parse(self, raw_texts: list[str]) -> Tuple[dict[str, Optional[str]], Optional[str]]:
        """
        Parse raw OCR texts into structured CNIC fields.
        
        Args:
            raw_texts: List of OCR text strings from detected regions
            
        Returns:
            Tuple of (dict with 8 CNIC fields, error_message or None)
        """
        logger.info(f"Parsing {len(raw_texts)} OCR regions")
        
        # Initialize result
        result = {
            "name": None,
            "father_name": None,
            "gender": None,
            "country_of_stay": None,
            "identity_number": None,
            "date_of_birth": None,
            "date_of_issue": None,
            "date_of_expiry": None,
        }
        
        # Clean and normalize all texts
        cleaned_texts = [self._normalize_text(t) for t in raw_texts if t and t.strip()]
        
        # Filter out noise (header text, "no text detected", etc.)
        filtered_texts = [t for t in cleaned_texts if self._is_meaningful(t)]
        
        logger.debug(f"Cleaned texts: {filtered_texts}")
        
        # First pass: Extract labeled fields (these take priority)
        for text in filtered_texts:
            text_lower = text.lower()
            
            # Identity Number (CNIC: XXXXX-XXXXXXX-X)
            if not result["identity_number"]:
                result["identity_number"] = self._extract_identity_number(text)
            
            # Dates (birth, issue, expiry)
            self._extract_dates(text, result)
            
            # Gender - prioritize extracting from labeled lines
            if not result["gender"]:
                result["gender"] = self._extract_gender(text)
            
            # Country of Stay
            if not result["country_of_stay"]:
                result["country_of_stay"] = self._extract_country(text)
            
            # Name - ONLY if "name" keyword is present
            if not result["name"] and "name" in text_lower:
                result["name"] = self._extract_name(text, is_father=False)
            
            # Father's Name - ONLY if "father" keyword is present
            if not result["father_name"] and "father" in text_lower:
                result["father_name"] = self._extract_name(text, is_father=True)
        
        # Second pass: standalone name extraction
        # If we still don't have name/father name, look for standalone names
        if not result["name"] or not result["father_name"]:
            self._extract_standalone_names(filtered_texts, result)
        
        # Clean and validate final result
        result = self._clean_result(result)
        
        # Validate critical fields
        validation_error = self._validate_result(result)
        if validation_error:
            logger.warning(f"Validation failed: {validation_error}")
            return result, validation_error
        
        logger.info(f"Final parsed data: {result}")
        return result, None
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by fixing common OCR typos."""
        text = text.strip()
        text_lower = text.lower()
        
        # Apply typo corrections
        for typo, correction in self.typo_corrections.items():
            text_lower = text_lower.replace(typo, correction)
        
        # Remove extra spaces
        text = " ".join(text.split())
        
        return text
    
    def _is_meaningful(self, text: str) -> bool:
        """Check if text contains meaningful data (not just headers/noise)."""
        text_lower = text.lower().strip()
        
        # Skip empty or very short text
        if len(text_lower) < 2:
            return False
        
        # Skip "no text detected"
        if "no text detected" in text_lower:
            return False
        
        # Skip pure header text
        noise_phrases = [
            "pakistan national identity card",
            "islamic republic of pakistan",
            "holder's signature",
            "holder signature",
            "national identity card",
            "national identity"
        ]
        
        if any(phrase == text_lower for phrase in noise_phrases):
            return False
        
        return True
    
    def _extract_identity_number(self, text: str) -> Optional[str]:
        """Extract CNIC identity number."""
        # Format: XXXXX-XXXXXXX-X
        match = re.search(r"\b(\d{5}[-\s]?\d{7}[-\s]?\d)\b", text)
        if match:
            # Normalize format with dashes
            raw = match.group(1).replace(" ", "").replace("-", "")
            if len(raw) == 13:
                return f"{raw[:5]}-{raw[5:12]}-{raw[12]}"
        return None
    
    def _extract_dates(self, text: str, result: dict) -> None:
        """Extract dates from text into result dict."""
        text_lower = text.lower()
        
        # Find all dates in format DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY
        date_pattern = r"\b(\d{2}[./-]\d{2}[./-]\d{4})\b"
        dates = re.findall(date_pattern, text)
        
        if not dates:
            return
        
        # Normalize dates to DD/MM/YYYY
        dates = [d.replace(".", "/").replace("-", "/") for d in dates]
        
        # If text contains keywords, use position-based matching
        keywords = {
            "birth": "date_of_birth",
            "issue": "date_of_issue",
            "expiry": "date_of_expiry",
        }
        
        # Map keywords to their position in text
        keyword_positions = []
        for keyword, field_name in keywords.items():
            if keyword in text_lower and not result[field_name]:
                pos = text_lower.find(keyword)
                keyword_positions.append((pos, field_name))
        
        # Sort by position
        keyword_positions.sort()
        
        # Match each keyword with the nearest following date
        date_positions = [(text.lower().find(d.replace("/", ".")), d) for d in dates if text.lower().find(d.replace("/", ".")) >= 0]
        if not date_positions:
            date_positions = [(text.lower().find(d.replace("/", "-")), d) for d in dates if text.lower().find(d.replace("/", "-")) >= 0]
        if not date_positions:
            date_positions = [(text.lower().find(d), d) for d in dates if text.lower().find(d) >= 0]
        
        date_positions.sort()
        
        used_dates = set()
        for kw_pos, field_name in keyword_positions:
            # Find first date after this keyword
            for date_pos, date_val in date_positions:
                if date_pos > kw_pos and date_val not in used_dates:
                    result[field_name] = date_val
                    used_dates.add(date_val)
                    logger.debug(f"Extracted {field_name}: {date_val}")
                    break
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender from text."""
        text_lower = text.lower()
        
        # Look for "gender" keyword or variations (gende, gendei, gendet)
        if any(kw in text_lower for kw in ["gender", "gende"]):
            # Find M or F anywhere in the text
            match = re.search(r"\b([MF])\b", text, re.IGNORECASE)
            if match:
                return "Male" if match.group(1).upper() == "M" else "Female"
        
        # Standalone M or F
        if re.match(r"^\s*[MF]\s*$", text, re.IGNORECASE):
            return "Male" if text.strip().upper() == "M" else "Female"
        
        return None
    
    def _extract_name(self, text: str, is_father: bool = False) -> Optional[str]:
        """Extract name or father's name from text."""
        text_lower = text.lower()
        
        if is_father:
            # Remove "father" keyword and clean
            text = re.sub(r"(?i)father'?s?\s+name\s*:?\s*", "", text)
        else:
            # Remove "name" keyword and clean
            text = re.sub(r"(?i)^name\s*:?\s*", "", text)
        
        text = text.strip()
        
        # Clean unwanted text
        text = re.sub(r"(?i)\b(pakistan|national|identity|card|islamic|republic)\b", "", text).strip()
        
        # Must be alphabetic with possible spaces and be reasonable length
        if re.match(r"^[A-Za-z ]{3,50}$", text) and len(text.split()) >= 2:
            return text.title()
        
        return None
    
    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a person's name."""
        # 2-4 words, alphabetic, reasonable length
        words = text.split()
        if 2 <= len(words) <= 4:
            if all(w.isalpha() for w in words) and 5 <= len(text) <= 40:
                return True
        return False
    
    def _extract_standalone_names(self, texts: list[str], result: dict) -> None:
        """Extract names from standalone text lines as fallback only."""
        potential_names = []
        
        for text in texts:
            text_clean = text.strip()
            
            # Skip if already has a keyword
            if any(kw in text.lower() for kw in ["father", "name", "gender", "date", "identity", "birth", "issue", "expiry", "country"]):
                continue
            
            # Check if looks like a name
            if self._looks_like_name(text_clean):
                potential_names.append(text_clean.title())
        
        # Standalone names are guessed in order: first is likely father's name, second is person's name
        # But ONLY use as fallback if we don't have labeled data
        if not result["father_name"] and len(potential_names) > 0:
            result["father_name"] = potential_names[0]
            logger.debug(f"Extracted father_name from standalone (fallback): {result['father_name']}")
        
        if not result["name"] and len(potential_names) > 1:
            result["name"] = potential_names[1]
            logger.debug(f"Extracted name from standalone (fallback): {result['name']}")
    
    def _extract_country(self, text: str) -> Optional[str]:
        """Extract country of stay from text."""
        text_lower = text.lower()
        
        # Look for "country" keyword variations
        if "country" in text_lower:
            # Remove the keyword and extract country name
            # Handle variations: "Country of Stay", "Country ofStay", "countryofstay"
            cleaned = re.sub(r"(?i)country\s*of\s*stay\s*:?\s*", "", text).strip()
            cleaned = re.sub(r"(?i)country\s*:?\s*", "", cleaned).strip()
            
            # Check if we have a valid country name
            if cleaned and len(cleaned) > 2 and cleaned.replace(" ", "").isalpha():
                return cleaned.title()
        
        return None
    
    def _clean_result(self, result: dict) -> dict:
        """Clean and validate final result."""
        # Remove leading/trailing spaces
        for key in result:
            if result[key] and isinstance(result[key], str):
                result[key] = result[key].strip()
        
        return result
    
    def _validate_result(self, result: dict) -> Optional[str]:
        """Validate extracted data quality. Returns error message if validation fails."""
        
        # Check if any critical field is missing
        required_fields = [
            'name', 'father_name', 'gender', 'country_of_stay',
            'identity_number', 'date_of_birth', 'date_of_issue', 'date_of_expiry'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not result[field] or result[field].strip() == "":
                missing_fields.append(field.replace('_', ' ').title())
        
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            return f"Image quality is poor. Could not detect: {fields_str}. Please provide a clearer image."
        
        # Validate dates (must be complete and valid)
        date_fields = ['date_of_birth', 'date_of_issue', 'date_of_expiry']
        for field in date_fields:
            if not self._is_valid_date(result[field]):
                return f"Image quality is poor. {field.replace('_', ' ').title()} is incomplete or invalid. Please provide a clearer image."
        
        # Validate country (must be a real country name)
        if not self._is_valid_country(result['country_of_stay']):
            return f"Image quality is poor. Country '{result['country_of_stay']}' appears invalid. Please provide a clearer image."
        
        return None
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid and complete."""
        try:
            # Try to parse DD/MM/YYYY format
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            
            # Check reasonable year range (1900-2100)
            if date_obj.year < 1900 or date_obj.year > 2100:
                return False
            
            # Check month and day are valid
            if date_obj.month < 1 or date_obj.month > 12:
                return False
            if date_obj.day < 1 or date_obj.day > 31:
                return False
            
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_valid_country(self, country: str) -> bool:
        """Check if country name is valid."""
        country_lower = country.lower().strip()
        
        # Check against known countries
        if country_lower in self.valid_countries:
            return True
        
        # If not in list, check if it at least looks like a country name
        # (alphabetic, reasonable length, not OCR garbage)
        if len(country_lower) < 3 or len(country_lower) > 30:
            return False
        
        # Should be mostly alphabetic
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in country_lower) / len(country_lower)
        if alpha_ratio < 0.8:
            return False
        
        # Check it's not OCR garbage (like "M" or "Gende")
        if country_lower in self.ignore_words:
            return False
        
        # Accept if it passes basic checks
        return True


# Singleton parser instance
cnic_parser = CNICParser()
