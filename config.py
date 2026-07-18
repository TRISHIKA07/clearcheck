"""
ComplianceCore AI Configuration File.
Holds all system configurations, constants, directories, rules, and model settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a local .env file
load_dotenv()

# --- Base Directories ---
BASE_DIR: Path = Path(__file__).resolve().parent
UPLOADS_DIR: Path = BASE_DIR / "uploads"
REPORTS_DIR: Path = BASE_DIR / "compliance_reports"
LOG_DIR: Path = BASE_DIR / "logs"

# Ensure essential directories exist
for directory in [UPLOADS_DIR, REPORTS_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# --- Logging Configuration ---
LOG_FILE_PATH: Path = LOG_DIR / "compliance_core.log"

# --- System & Model Configuration ---
# The local Ollama server typically binds to http://localhost:11434.
# We can configure the model name and other inference settings.
GEMMA_MODEL_NAME: str = os.getenv("GEMMA_MODEL_NAME", "gemma4:e4b")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180.0"))
OLLAMA_MAX_RETRIES: int = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))

# --- OCR Configuration ---
# PyTesseract executable path override (if needed in Windows and not in system PATH)
# Example: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")

# --- Compliance Workflow Constants ---
SUPPORTED_DOC_TYPES: list[str] = [
    "Passport", 
    "Aadhaar Card", 
    "PAN Card", 
    "Driving License", 
    "Utility Bill", 
    "Bank Statement PDF"
]

# Risk weights for deterministic compliance rules
# Used by the risk engine to calculate a final numerical score (0 - 100)
# A combination of rule failures determines the base score.
RULE_RISK_WEIGHTS: dict[str, float] = {
    "PAN_VALIDATION": 10.0,
    "AADHAAR_VALIDATION": 10.0,
    "MISSIC_KYC": 15.0,
    "MISSING_DOB": 15.0,
    "MISSING_ADDRESS": 15.0,
    "IDENTITY_MISMATCH": 25.0,
    "DUPLICATE_IDENTITY": 15.0,
    "EXPIRED_DOCUMENTS": 20.0,
    "INCOMPLETE_ONBOARDING": 10.0,
    "STRUCTURING_BEHAVIOUR": 30.0,
    "HIGH_VALUE_BURSTS": 25.0,
    "REPEATED_BENEFICIARIES": 15.0,
    "SUSPICIOUS_KEYWORDS": 20.0,
    "CROSS_BORDER_INDICATORS": 20.0,
}

# Thresholds for transaction analysis
TXN_HIGH_VALUE_THRESHOLD: float = 100000.0  # in base currency, e.g., INR 1 Lakh
TXN_VELOCITY_WINDOW_DAYS: int = 7
TXN_VELOCITY_SPIKE_STD_DEV: float = 3.0       # Spikes exceeding 3 standard deviations
TXN_BURST_COUNT_LIMIT: int = 5                # More than 5 transactions in a short duration
TXN_BURST_WINDOW_MINUTES: int = 60            # 1 hour window for transaction bursts
SUSPICIOUS_DESCRIPTION_KEYWORDS: list[str] = [
    "gaming", "casino", "betting", "crypto", "bitcoin", "mixer", "refund", "gift", 
    "monero", "darknet", "hawala", "cash-in", "structuring", "loan payoff"
]

# --- Reporting Configuration ---
MAX_REPORT_PAGES: int = 10
AUDIT_FILENAME_TEMPLATE: str = "{date}_{risk_level}_audit_report"