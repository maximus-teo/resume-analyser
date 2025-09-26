from pdfminer.high_level import extract_text
import re
from collections import Counter
import spacy
import string
import json
nlp = spacy.load("en_core_web_sm")

def extract_pdf_text(file_path: str) -> str:
    return extract_text(file_path)

def extract_keywords(text):
    # identify noun chunks with spacy (filter out stop words)
    # also strip whitespace and convert to lowercase
    doc = nlp(text)
    keywords = set()
    for chunk in doc.noun_chunks:
        token = chunk.text.lower().strip()
        if token not in nlp.Defaults.stop_words: keywords.add(token)
    return keywords

def match_score(resume_text: str, job_text: str, job_category: str):
    resume_words = extract_keywords(resume_text)
    job_words = extract_keywords(job_text)
    matched = resume_words & job_words
    missing = job_words - resume_words
    score = len(matched) / len(job_words) * 100
    bonus = 0

    # matched & relevant hard/soft will get a higher weightage and featured 1st
    matched_relevant_hard = set()
    matched_relevant_soft = set()

    # missing & relevant hard/soft will be featured 3rd 
    missing_relevant_hard = set()
    missing_relevant_soft = set()

    hard_skills_path = 'app/assets/skills_fallback.json'
    soft_skills_path = ''
    if (job_category != "fallback"): 
        hard_skills_path = f'app/assets/skills_{job_category}_hard.json'
        soft_skills_path = f'app/assets/skills_{job_category}_soft.json'

    with open(hard_skills_path,'r') as f:
        hard_skills = {item.lower() for item in set(json.load(f))}
        relevant_job_words = job_words & hard_skills # relevant words from jobdesc
        relevant_resume_words = resume_words & hard_skills # relevant words from resume
        bonus += len(relevant_job_words & relevant_resume_words) # bonus points for hard skills that are in both resume and job desc
        matched_relevant_hard = relevant_job_words & relevant_resume_words
        missing_relevant_hard = relevant_job_words - relevant_resume_words

    with open(soft_skills_path, 'r') as f:
        soft_skills = {item.lower() for item in set(json.load(f))}
        relevant_job_words = job_words & soft_skills # relevant words from jobdesc
        relevant_resume_words = resume_words & soft_skills # relevant words from resume
        if (soft_skills_path != ''): bonus += len(relevant_job_words & relevant_resume_words) # bonus points for soft skills that are in both resume and job desc
        matched_relevant_soft = relevant_job_words & relevant_resume_words
        missing_relevant_soft = relevant_job_words - relevant_resume_words

    # matched & not sure will be featured 2nd
    matched_notsure = matched - (matched_relevant_hard | matched_relevant_soft)
    # missing & not sure will be featured 4th
    missing_notsure = missing - (missing_relevant_hard | missing_relevant_soft)
    score += bonus
    return (round(score, 2), round(bonus,2),
            matched_relevant_hard, matched_relevant_soft, matched_notsure,
            missing_relevant_hard, missing_relevant_soft, missing_notsure)