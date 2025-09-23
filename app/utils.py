from pdfminer.high_level import extract_text
import re
from collections import Counter

def extract_pdf_text(file_path: str) -> str:
    return extract_text(file_path)

def extract_keywords(text: str) -> set:
    # split on non-letters, lowercase, filter out short words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return set(words)

def match_score(resume_text: str, job_text: str):
    resume_words = extract_keywords(resume_text)
    job_words = extract_keywords(job_text)
    overlap = resume_words & job_words
    score = len(overlap) / len(job_words) * 100
    missing = job_words - resume_words
    return round(score, 2), overlap, missing