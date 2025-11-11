from pdfminer.high_level import extract_text
import spacy
import json
import numpy as np
from pathlib import Path
from collections import Counter

nlp = spacy.load("en_core_web_md")  # use medium model for semantic similarity

# Section definitions
info_categories = {
    "EDUCATION": {"weight": 2, "headers": ["education", "academic", "degree", "certification", "qualification"]},
    "EXPERIENCE": {"weight": 3, "headers": ["experience", "employment", "projects", "work history", "responsibilities"]},
    "SKILLS": {"weight": 4, "headers": ["skills", "technologies", "expertise", "proficiencies", "languages"]},
    "OTHER": {"weight": 1, "headers": []},
}

def extract_pdf_text(file_path: str):
    return extract_text(file_path)


def preprocess_text(text: str):
    """Lowercase, remove excessive whitespace."""
    return " ".join(text.lower().split())


def get_hard_skills_list(category: str):
    """Load curated skills JSON based on job category."""
    try:
        skills_path = Path(f"app/assets/skills_{category}_hard.json")
        with open(skills_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [s.lower() for s in data]
    except Exception:
        return []
    
def segment_sections(text: str):
    """Roughly segment text into sections based on common resume/JD headers"""
    sections = {"EXPERIENCE": "", "EDUCATION": "", "SKILLS": "", "OTHER": ""}
    current_section = "OTHER" # by default
    lines = text.splitlines()

    for line in lines:
        line = line.lower().strip()
        found = False
        for section, info in info_categories.items():
            if any(h in line for h in info["headers"]):
                current_section = section
                found = True
                break
        if not found:
            sections[current_section] += " " + line
    
    return sections


def extract_keywords(text: str):
    """Extract meaningful noun chunks and keywords."""
    doc = nlp(text)
    chunks = [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 1]
    tokens = [token.lemma_.lower() for token in doc if token.pos_ in ("NOUN", "PROPN", "VERB")]
    return list(set(chunks + tokens))


def semantic_match_score(resume_tokens, jd_tokens):
    """Compute semantic similarity between resume and JD tokens."""
    if not resume_tokens or not jd_tokens:
        return 0.0

    resume_doc = nlp(" ".join(resume_tokens))
    jd_doc = nlp(" ".join(jd_tokens))
    similarity = resume_doc.similarity(jd_doc)
    return similarity  # 0–1 range


def compute_tfidf_like_weighting(tokens):
    """Approximate TF-IDF weighting using term frequency normalization."""
    freq = Counter(tokens)
    total = sum(freq.values())
    return {word: freq[word] / total for word in freq}


def section_weighted_score(resume_sections, job_text, hard_skills):
    """Compute weighted section score using TF-IDF and semantic similarity."""
    total_weighted = 0
    total_weights = 0
    matched_skills = []

    for section, text in resume_sections.items():
        if not text.strip():
            continue

        weight = info_categories.get(section, {"weight": 1})["weight"]
        tokens = extract_keywords(text)
        tfidf_weights = compute_tfidf_like_weighting(tokens)

        # Direct matches (hard skills)
        matched_skills = [skill for skill in hard_skills if skill in text and skill in job_text]

        # Semantic similarity to job description
        semantic_score = semantic_match_score(tokens, extract_keywords(job_text))

        # Section contribution
        section_score = weight * (0.5 * semantic_score + 0.5 * min(len(matched_skills) / max(len(hard_skills), 1), 1.0))
        total_weighted += section_score
        total_weights += weight

    avg_score = total_weighted / max(total_weights, 1)
    return avg_score, matched_skills

def get_weighted_score(resume_text: str, job_text: str, category: str):
    """Compute a weighted score (0–100) for resume vs job description."""

    #resume_text = preprocess_text(resume_text)
    #job_text = preprocess_text(job_text)
    jd_tokens = extract_keywords(job_text)

    hard_skills = get_hard_skills_list(category)
    resume_sections = segment_sections(resume_text)
    print(resume_sections)

    section_score, matched_skills = section_weighted_score(resume_sections, job_text, hard_skills)

    # Keyword density = unique matched keywords / total JD keywords
    unique_matches = len(set(matched_skills))
    density = unique_matches / max(len(hard_skills), 1)
    density = np.clip(density, 0, 1)

    semantic_score = semantic_match_score(extract_keywords(resume_text), jd_tokens)

    # Blend section and density scores
    final_score = 0.7 * section_score + 0.2 * density + 0.1 * semantic_score

    # Normalize: enforce floor at 25, cap at 95
    normalised_score = np.clip(25 + final_score * 75, 0, 100)

    print("section score:", section_score, "density:", density, "semantic_score:", semantic_score, "matched skills:", matched_skills)

    return (round(normalised_score), round(section_score*100,2), round(density*100,2), matched_skills, round(semantic_score * 100,2))
