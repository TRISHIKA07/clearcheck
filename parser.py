"""
ComplianceCore AI Identity Parser Module.
Processes raw OCR text deterministically to extract customer profile details.
Does NOT call Gemma or any LLM; relies on regular expressions and text normalisation.
"""

import re
import logging
from typing import Optional, Any, List
from utils import clean_ocr_text
from models import CustomerProfile

logger = logging.getLogger("ComplianceCore.Parser")

def extract_dates(text: str) -> List[str]:
    """
    Extracts all dates matching DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD or DD MMM YYYY.
    """
    # Regex patterns for standard dates
    patterns = [
        r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",     # 15/08/1947 or 15-08-1947
        r"\b\d{4}[/-]\d{2}[/-]\d{2}\b",     # 1947-08-15
        r"\b\d{2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}\b" # 15 Aug 1947 / 15 August 1947
    ]
    
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if m not in dates:
                dates.append(m)
    return dates

def parse_customer_profile(raw_text: str) -> CustomerProfile:
    """
    Parses normalized OCR text using deterministic Python string & regex methods.
    Returns a typed CustomerProfile dataclass.
    """
    cleaned_text = clean_ocr_text(raw_text)
    lines = cleaned_text.split("\n")
    
    profile = CustomerProfile()
    
    # --- 1. Regex Extractions (IDs) ---
    
    # PAN Card (Format: 5 Letters, 4 Digits, 1 Letter)
    pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", cleaned_text)
    if pan_match:
        profile.pan = pan_match.group(0)
        logger.info(f"Parsed PAN: {profile.pan}")
        
    # Aadhaar Number (12 digits, often with space/hyphen grouping)
    aadhaar_match = re.search(r"\b[2-9][0-9]{3}[\s-][0-9]{4}[\s-][0-9]{4}\b", cleaned_text)
    if aadhaar_match:
        profile.aadhaar = aadhaar_match.group(0).replace(" ", "").replace("-", "")
        logger.info(f"Parsed Aadhaar: {profile.aadhaar}")
    else:
        # Check for continuous 12 digits
        aadhaar_raw = re.search(r"\b[2-9][0-9]{11}\b", cleaned_text)
        if aadhaar_raw:
            profile.aadhaar = aadhaar_raw.group(0)
            logger.info(f"Parsed Aadhaar: {profile.aadhaar}")

    # Passport Number (Typically starts with letter followed by 7 digits)
    passport_match = re.search(r"\b[A-Z][0-9]{7}\b", cleaned_text)
    if passport_match:
        profile.passport_number = passport_match.group(0)
        logger.info(f"Parsed Passport Number: {profile.passport_number}")
        
    # Driving License (State code + 2 digits + Year/Serial - 13 to 15 alphanumeric)
    dl_patterns = [
        r"\b[A-Z]{2}[0-9]{2}[ -]?[0-9]{11}\b",
        r"\b[A-Z]{2}[ -]?[0-9]{13,14}\b"
    ]
    for pattern in dl_patterns:
        dl_match = re.search(pattern, cleaned_text)
        if dl_match:
            profile.driving_license_number = dl_match.group(0).replace(" ", "").replace("-", "")
            logger.info(f"Parsed Driving License: {profile.driving_license_number}")
            break

    # --- 2. Date Extractions (DOB, Issue Date, Expiry Date) ---
    all_dates = extract_dates(cleaned_text)
    
    # Walk line-by-line to look for dates with keywords
    for line in lines:
        lower_line = line.lower()
        line_dates = extract_dates(line)
        if not line_dates:
            continue
            
        # DOB Keywords
        if any(kw in lower_line for kw in ["dob", "date of birth", "birth", "d.o.b", "yob"]):
            profile.dob = line_dates[0]
            logger.info(f"Parsed DOB: {profile.dob}")
            
        # Expiry Keywords
        if any(kw in lower_line for kw in ["expiry", "expire", "valid upto", "valid till", "valid to", "exp"]):
            profile.expiry_date = line_dates[0]
            logger.info(f"Parsed Expiry Date: {profile.expiry_date}")
            
        # Issue Date Keywords
        if any(kw in lower_line for kw in ["issue", "issued", "doi", "date of issue", "iss"]):
            profile.issue_date = line_dates[0]
            logger.info(f"Parsed Issue Date: {profile.issue_date}")

    # Fallbacks for Dates if keywords not found but dates exist
    if not profile.dob and len(all_dates) > 0:
        # Usually, DOB is the oldest date in an ID card
        # (Though not guaranteed, it is a reasonable deterministic fallback or we leave it blank)
        # Let's keep it safe: if there's only 1 date and DOB keyword didn't match but we have DOB label, or similar
        pass

    # --- 3. Customer Name ---
    # Look for name label
    name_found = False
    for i, line in enumerate(lines):
        lower_line = line.lower()
        if "name" in lower_line and not any(kw in lower_line for kw in ["father", "mother", "spouse", "issue"]):
            # Split by colon or equal to get the value
            parts = re.split(r"[:=]", line)
            if len(parts) > 1 and len(parts[1].strip()) > 2:
                profile.name = parts[1].strip()
                name_found = True
                logger.info(f"Parsed Name from keyword line: {profile.name}")
                break
                
    # Fallback name extraction for specific IDs if name label not matched
    if not name_found:
        # PAN Cards often contain name on line 3 or 4 (after INCOME TAX DEPARTMENT)
        for i, line in enumerate(lines):
            if "income tax department" in line.lower() and i + 1 < len(lines):
                # The next non-empty line after title is usually name
                candidate = lines[i+1].strip()
                if candidate and not candidate.lower().startswith("govt") and len(candidate.split()) >= 2:
                    profile.name = candidate
                    logger.info(f"Parsed PAN Card Name fallback: {profile.name}")
                    name_found = True
                    break
                    
    # --- 4. Address Extraction ---
    address_lines = []
    in_address_block = False
    for line in lines:
        lower_line = line.lower()
        if "address" in lower_line or "permanent address" in lower_line:
            in_address_block = True
            # Extract anything after colon
            parts = re.split(r"[:=]", line)
            if len(parts) > 1 and len(parts[1].strip()) > 3:
                address_lines.append(parts[1].strip())
            continue
            
        if in_address_block:
            # End block if we hit another field or blank line
            if not line.strip() or any(kw in lower_line for kw in ["pin", "tel", "phone", "signature", "photo", "date"]):
                # If there's a pin code in this line, keep it as part of address before ending
                if "pin" in lower_line or re.search(r"\b\d{6}\b", line):
                    address_lines.append(line.strip())
                in_address_block = False
            else:
                address_lines.append(line.strip())
                
    if address_lines:
        profile.address = ", ".join(address_lines)
        logger.info(f"Parsed Address: {profile.address}")

    # --- 5. Utility Bill Information ---
    utility_keywords = ["electricity", "bses", "water board", "utility", "consumer number", "consumer no", "biller"]
    if any(kw in cleaned_text.lower() for kw in utility_keywords):
        bill_info = []
        # Find account / consumer numbers
        consumer_match = re.search(r"(?:consumer|account|customer|bill)\s*(?:no|num|number)?\s*[:\-=]?\s*([A-Z0-9\-]+)", cleaned_text, re.IGNORECASE)
        if consumer_match:
            bill_info.append(f"Consumer/Account: {consumer_match.group(1)}")
        
        # Check Biller Name
        for line in lines:
            if any(kw in line.lower() for kw in ["ltd", "board", "power", "discom", "utility", "telecom"]):
                bill_info.append(f"Biller: {line.strip()}")
                break
                
        if bill_info:
            profile.utility_bill_info = " | ".join(bill_info)
            logger.info(f"Parsed Utility Bill Info: {profile.utility_bill_info}")

    # --- 6. Bank Statement Information ---
    bank_keywords = ["bank", "statement", "statement of account", "transaction history"]
    if any(kw in cleaned_text.lower() for kw in bank_keywords):
        bank_info = []
        # Find bank name
        for line in lines:
            if "bank" in line.lower() and len(line) < 50:
                bank_info.append(f"Bank Name: {line.strip()}")
                break
        
        # Find account number
        acct_match = re.search(r"(?:account|a/c|acct|acc)\s*(?:no|num|number)?\s*[:\-=]?\s*([0-9]{9,18})", cleaned_text, re.IGNORECASE)
        if acct_match:
            bank_info.append(f"Account No: {acct_match.group(1)}")
            
        # Find IFSC Code
        ifsc_match = re.search(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", cleaned_text)
        if ifsc_match:
            bank_info.append(f"IFSC: {ifsc_match.group(0)}")
            
        if bank_info:
            profile.bank_statement_info = " | ".join(bank_info)
            logger.info(f"Parsed Bank Statement Info: {profile.bank_statement_info}")

    return profile
