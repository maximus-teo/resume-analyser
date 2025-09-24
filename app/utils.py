from pdfminer.high_level import extract_text
import re
from collections import Counter
import spacy
nlp = spacy.load("en_core_web_sm")

def extract_pdf_text(file_path: str) -> str:
    return extract_text(file_path)

def extract_keywords(text):
    # use spacy to parse out noun chunks into a list and filter out NLP stop words
    doc = nlp(text)
    keywords = set()
    for chunk in doc.noun_chunks:
        token = chunk.text.lower().strip()
        if len(token) > 2 and token not in nlp.Defaults.stop_words:
            keywords.add(token)
    return keywords

def match_score(resume_text: str, job_text: str):
    resume_words = extract_keywords(resume_text)
    job_words = extract_keywords(job_text)
    overlap = resume_words & job_words
    score = len(overlap) / len(job_words) * 100
    missing = job_words - resume_words
    return round(score, 2), overlap, missing