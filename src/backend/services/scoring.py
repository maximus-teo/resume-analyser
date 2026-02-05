import spacy
import json
import numpy as np
import re
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Any, Optional

# Load spacy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Spacy model 'en_core_web_md' not found. Downloading...")
    from spacy.cli import download
    download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

# Section definitions
INFO_CATEGORIES = {
    "SKILLS": {
        "weight": 4,
        "headers": ["skills", "technologies", "expertise", "proficiencies", "languages", "tools", "interest"]},
    "EXPERIENCE": {
        "weight": 3,
        "headers": ["experience", "employment", "projects", "work history", "responsibilities"]},
    "EDUCATION": {
        "weight": 2,
        "headers": ["education", "enrolled", "academic", "degree", "certification", "qualification", "post-secondary", "bachelor", "master", "doctorate", "phd"]},
    "OTHER": {
        "weight": 1,
        "headers": []},
}

def get_keywords_list(category: str) -> List[str]:
    """Load curated skills JSON based on job category."""
    try:
        skills_path = Path(f"src/frontend/static/data/keywords_{category}.json") 
        if not skills_path.exists():
             skills_path = Path(f"app/assets/keywords_{category}.json")

        if skills_path.exists():
            with open(skills_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [s.lower() for s in data]
        return []
    except Exception:
        return []

def segment_sections(text: str) -> Dict[str, str]:
    """Roughly segment text into sections based on common resume/JD headers"""
    sections = {"EXPERIENCE": "", "EDUCATION": "", "SKILLS": "", "OTHER": ""}
    current_section = "OTHER" # by default
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        found = False
        for section, info in INFO_CATEGORIES.items():
            if (len(line.split()) < 5) and any(h in line.lower() for h in info["headers"]):
                current_section = section
                found = True
                break
        if not found:
            if sections[current_section] == "": sections[current_section] = line
            else: sections[current_section] += "%nl%" + line
    return sections

def extract_keywords(text: str) -> List[str]:
    """Extract meaningful noun chunks and keywords, no stop words."""
    doc = nlp(text)
    chunks = [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 1]
    return list(set(chunks))

def semantic_match_score(resume_tokens: List[str], jd_tokens: List[str]) -> float:
    """Compute semantic similarity between resume and JD tokens."""
    if not resume_tokens or not jd_tokens:
        return 0.0

    resume_doc = nlp(" ".join(resume_tokens))
    jd_doc = nlp(" ".join(jd_tokens))
    similarity = resume_doc.similarity(jd_doc)
    return similarity

def tokenize(text: str) -> List[str]:
    """Lowercase, whitespace tokenization with punctuation stripped."""
    return [
        re.sub(r"[^a-zA-Z0-9]", "", t)
        for t in text.lower().split()
        if re.sub(r"[^a-zA-Z0-9]", "", t)
    ]

def find_keyword_occurrences(tokens, keyword_tokens):
    """Yield start indices where keyword_tokens appear in tokens."""
    k = len(keyword_tokens)
    for i in range(len(tokens) - k + 1):
        if tokens[i:i+k] == keyword_tokens:
            yield i

def extract_context(tokens, start_idx, kw_len, window=3):
    """Returns context up to 3 words before and after a given token/keyword."""
    before_start = max(0, start_idx - window)
    after_end = min(len(tokens), start_idx + kw_len + window)

    before = " ".join(tokens[before_start:start_idx])
    after = " ".join(tokens[start_idx + kw_len:after_end])

    return before, after

def section_weighted_score(resume_sections, job_text, keywords): 
    resume_weight = 0
    jd_weight = 0
    section_scores = [0.0, 0.0, 0.0, 0.0] # others (1), education (2), experience (3), skills (4)

    matched_keywords = {} # dictionary: keyword, weight
    jd_keywords = {} # dictionary: keyword, weight
    missing_keywords = {} # dictionary: keyword, context

    skills_wgt = INFO_CATEGORIES.get("SKILLS", {"weight": 4})["weight"]
    extra_keywords = []

    # parsing words - classify as extra keywords not found in keyword database
    for line in job_text.splitlines():
        for word in line.split():
            if sum(1 for char in word if char.isupper()) >= 2 and word not in keywords: 
                extra_keywords.append(word.lower())

    # add all extra_keywords to jd_keywords
    for kw in extra_keywords:
        jd_keywords.update({kw: skills_wgt})

    # add relevant keywords from database to jd_keywords
    for kw in keywords:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, job_text.lower()):
            jd_keywords.update({kw: skills_wgt})

    # build matched keywords dictionary
    for section, res_text in resume_sections.items():
        if not res_text.strip():
            continue

        weight = INFO_CATEGORIES.get(section, {"weight": 1})["weight"]

        for kw in keywords:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, res_text.lower()) and re.search(pattern, job_text.lower()) and kw not in matched_keywords:
                matched_keywords.update({kw: weight})
                jd_keywords.update({kw: weight}) 
        if extra_keywords:
            for kw in extra_keywords:
                pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                if re.search(pattern, res_text.lower()) and kw not in matched_keywords:
                    matched_keywords.update({kw: skills_wgt})

    # build missing keywords dictionary with context extraction
    jd_tokens = tokenize(job_text)

    for kw, wgt in jd_keywords.items():
        if kw in matched_keywords:
            continue

        kw_tokens = tokenize(kw)
        contexts = []

        for idx in find_keyword_occurrences(jd_tokens, kw_tokens):
            before, after = extract_context(jd_tokens, idx, len(kw_tokens))
            contexts.append([before, after])

        if contexts:
            missing_keywords[kw] = contexts[0]
        else:
            missing_keywords[kw] = ["", ""]
            
    section_scores_jd = [0.0, 0.0, 0.0, 0.0]
    section_scores_res = [0.0, 0.0, 0.0, 0.0]

    for kw, wgt in jd_keywords.items():
        if wgt > 0: section_scores_jd[wgt-1] += wgt
        jd_weight += wgt
    for kw, wgt in matched_keywords.items():
        if wgt > 0: section_scores_res[wgt-1] += wgt
        resume_weight += wgt

    for k in range(0,len(section_scores)):
        section_scores[k] = round(section_scores_res[k] / max(section_scores_jd[k],1) * 100, 2)

    avg_score = resume_weight / max(jd_weight, 1)
    density = len(matched_keywords) / max(len(jd_keywords), 1)

    jd_keywords = {key: val for key, val in sorted(jd_keywords.items())}
    matched_keywords = {key: val for key, val in sorted(matched_keywords.items())}

    return avg_score, section_scores, density, matched_keywords, missing_keywords

def calculate_ai_score(resume_skills: List[str], jd_required: List[str], jd_nice_to_have: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Calculate score based on strict matching of AI-extracted skills.
    Returns: (score (0-100), matched_skills, missing_skills)
    """
    if not jd_required:
        return 0.0, [], []
    
    resume_skills_norm = {s.lower() for s in resume_skills}
    required_norm = {s.lower() for s in jd_required}
    nice_norm = {s.lower() for s in jd_nice_to_have}
    
    matched = []
    missing = []
    
    # Check required
    required_hits = 0
    for req in required_norm:
        if req in resume_skills_norm:
            required_hits += 1
            matched.append(req)
        else:
            missing.append(req)
            
    # Check nice to have
    nice_hits = 0
    for nice in nice_norm:
        if nice in resume_skills_norm:
            nice_hits += 1
            matched.append(nice)
            
    # Score calculation
    # Weighted: Required skills are 80% of score, Nice to have are 20%
    # If no nice to have, Required is 100%
    
    req_score = (required_hits / len(required_norm)) * 100 if required_norm else 0
    
    if nice_norm:
        nice_score = (nice_hits / len(nice_norm)) * 100
        final_score = (req_score * 0.8) + (nice_score * 0.2)
    else:
        final_score = req_score
        
    return round(final_score, 2), matched, missing

def get_weighted_score(resume_text: str, job_text: str, category: str, 
                       ai_resume_skills: List[str] = None, 
                       ai_jd_required: List[str] = None,
                       ai_jd_nice: List[str] = None):

    # Legacy Keyword Calculation
    keywords = get_keywords_list(category)
    resume_sections = segment_sections(resume_text)

    keyword_score, section_scores, density, matched_keywords, missing_keywords = section_weighted_score(resume_sections, job_text, keywords)

    resume_tokens = extract_keywords(resume_text)
    jd_tokens = extract_keywords(job_text)
    semantic_score = semantic_match_score(resume_tokens, jd_tokens)

    # Legacy final score
    legacy_score = keyword_score * (0.6 + 0.4 * semantic_score) * 100
    
    final_score = legacy_score
    
    # If AI data is provided, mix it in
    if ai_resume_skills and ai_jd_required:
        ai_score, ai_matched, ai_missing = calculate_ai_score(ai_resume_skills, ai_jd_required, ai_jd_nice or [])
        # Blend: 60% legacy, 40% AI (or any other ratio)
        # Assuming AI is more accurate for "Skills" but Legacy is better for "Experience" density
        final_score = (legacy_score * 0.6) + (ai_score * 0.4)
        print("ai_score:", ai_score, "ai_matched:", ai_matched, "ai_missing:", ai_missing)
        print("legacy score:", legacy_score, "ai_score:", ai_score, "final_score:", final_score)
        
        # Merge matched keywords for display?
        # for now just return the blended score and let the legacy 'missing' keywords stand as they have context.
    
    resume_sections = {
        section: text.split("%nl%")
        for section, text in resume_sections.items()
        }

    return (round(final_score,2),
            round(keyword_score*100,2),
            resume_sections,
            section_scores,
            round(density*100,2),
            matched_keywords,
            missing_keywords,
            round(semantic_score * 100,2))
