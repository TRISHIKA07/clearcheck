"""
ComplianceCore AI Utilities Module.
Contains helper functions for logging, file verification, and text cleaning.
"""

import logging
import re
from pathlib import Path
from typing import Set
from config import LOG_FILE_PATH

def setup_logging() -> logging.Logger:
    """
    Configures application-wide logging to both console and log file.
    Returns the root logger.
    """
    logger = logging.getLogger("ComplianceCore")
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # File handler
        try:
            file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to standard print if logging file cannot be created
            print(f"Failed to initialize file logging handler: {e}")
            
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
    return logger

# Initialize logging for this module
logger = setup_logging()

def validate_file(file_path: Path, allowed_extensions: Set[str]) -> bool:
    """
    Validates if a file exists, is a file, and has an allowed extension.
    """
    try:
        if not file_path.exists():
            logger.error(f"File validation failed: File does not exist at {file_path}")
            return False
        if not file_path.is_file():
            logger.error(f"File validation failed: Path is not a file: {file_path}")
            return False
        
        suffix = file_path.suffix.lower().lstrip(".")
        if suffix not in allowed_extensions:
            logger.error(f"File validation failed: Extension '.{suffix}' not in allowed: {allowed_extensions}")
            return False
            
        return True
    except Exception as e:
        logger.exception(f"Unexpected error validating file: {e}")
        return False

def clean_ocr_text(text: str) -> str:
    """
    Normalizes OCR-extracted text by:
    - Cleaning double spaces/tabs.
    - Standardizing newlines.
    - Stripping trailing/leading whitespaces on each line.
    - Normalizing common misread characters if appropriate.
    """
    if not text:
        return ""
        
    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Strip leading/trailing spaces from each line, filter out empty lines if necessary
    lines = [line.strip() for line in text.split("\n")]
    
    # Reassemble and clean multiple spaces inside lines
    cleaned_lines = []
    for line in lines:
        if line:
            # Replace multiple whitespace characters with a single space
            line = re.sub(r"\s+", " ", line)
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines)

def safe_read_file(file_path: Path) -> Optional[bytes]:
    """
    Safely reads binary data from a file with exception handling.
    """
    try:
        if not file_path.is_file():
            return None
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.exception(f"Failed to read file {file_path}: {e}")
        return None
