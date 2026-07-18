"""
ComplianceCore AI OCR Module.
Handles text extraction from digital PDFs, scanned PDFs, and image files (PNG, JPG, JPEG)
using PyMuPDF and local Tesseract OCR.
"""

import logging
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

import config
from utils import setup_logging, validate_file

logger = logging.getLogger("ComplianceCore.OCR")

# Set pytesseract executable path if specified in config
if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

def ocr_image(image_bytes: bytes) -> str:
    """
    Runs Tesseract OCR on raw image bytes.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Optional: Convert image to grayscale for better OCR accuracy
        if image.mode != "L":
            image = image.convert("L")
            
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Failed to OCR image: {e}")
        raise e

def ocr_pdf_page_as_image(page: fitz.Page, zoom: float = 2.0) -> str:
    """
    Renders a PDF page to a high-resolution image and runs Tesseract OCR.
    """
    try:
        # Increase resolution (zoom) for better OCR accuracy
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        image_bytes = pix.tobytes("png")
        
        # Load in PIL and OCR
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Failed to render and OCR PDF page {page.number}: {e}")
        return ""

def extract_text_from_file(file_path: Path) -> Optional[str]:
    """
    Extracts text from a document. Automatically determines the file type and
    combines PyMuPDF text extraction with Tesseract OCR if text is not directly copyable.
    """
    logger.info(f"Starting text extraction for file: {file_path}")
    
    allowed_exts = {"pdf", "png", "jpg", "jpeg"}
    if not validate_file(file_path, allowed_exts):
        logger.error(f"Skipping OCR. File type not supported or invalid: {file_path}")
        return None
        
    suffix = file_path.suffix.lower().lstrip(".")
    
    # Process Images
    if suffix in {"png", "jpg", "jpeg"}:
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            text = ocr_image(image_bytes)
            logger.info("Successfully extracted text from image.")
            return text
        except Exception as e:
            logger.error(f"Error OCR-ing image file {file_path}: {e}")
            return None
            
    # Process PDFs
    if suffix == "pdf":
        try:
            doc = fitz.open(file_path)
            extracted_pages = []
            
            for page in doc:
                # 1. Try to extract digital text directly
                page_text = page.get_text()
                
                # If page text is very sparse (e.g. less than 20 chars), assume it's scanned
                if len(page_text.strip()) < 20:
                    logger.info(f"Page {page.number} appears scanned. Falling back to OCR...")
                    page_text = ocr_pdf_page_as_image(page)
                    
                extracted_pages.append(page_text)
                
            doc.close()
            combined_text = "\n--- PAGE BREAK ---\n".join(extracted_pages)
            logger.info("Successfully extracted text from PDF file.")
            return combined_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF file {file_path}: {e}")
            return None

    return None
