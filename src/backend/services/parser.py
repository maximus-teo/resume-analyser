from pdfminer.high_level import extract_text
import re

def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        return extract_text(file_path)
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def preprocess_text(text: str) -> str:
    """Basic text preprocessing."""
    return text.lower()
