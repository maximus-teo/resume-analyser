from pdfminer.high_level import extract_text
import spacy
import json
import numpy as np
from pathlib import Path
from collections import Counter

nlp = spacy.load("en_core_web_md")  # use medium model for semantic similarity

# how to determine mandatory requirements (must haves) for qualifications
# e.g. years of experience, degree equivalent, etc.
# more details on matched or missing
# show what sections contribute to the score

# database: SQLite to store past analyses? or keywords instead of json files.
# user accounts: auth with JWT if time allows

# Section definitions
info_categories = {
    "EDUCATION": {"weight": 2, "headers": ["education", "academic", "degree", "certification", "qualification"]},
    "EXPERIENCE": {"weight": 3, "headers": ["experience", "employment", "projects", "work history", "responsibilities"]},
    "SKILLS": {"weight": 4, "headers": ["skills", "technologies", "expertise", "proficiencies", "languages", "tools"]},
    "OTHER": {"weight": 1, "headers": []},
}

def extract_pdf_text(file_path: str):
    return extract_text(file_path)

def preprocess_text(text: str):
    return "".join(text.lower())

def get_keywords_list(category: str):
    """Load curated skills JSON based on job category."""
    try:
        skills_path = Path(f"app/assets/keywords_{category}.json")
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
            # not a cut and dried solution but a line must have <5 words to be a header
            # if the entire line matches any header in info_cat, start new section
            if (len(line.split()) < 5) and any(h in line for h in info["headers"]):
                current_section = section
                found = True
                break
        if not found:
            sections[current_section] += " " + line
    
    return sections


def extract_keywords(text: str):
    """Extract meaningful noun chunks and keywords, no stop words."""
    doc = nlp(text)
    chunks = [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 1]
    #tokens = [token.lemma_.lower() for token in doc if token.pos_ in ("NOUN", "PROPN", "VERB")]
    return list(set(chunks))


def semantic_match_score(resume_tokens, jd_tokens):
    """Compute semantic similarity between resume and JD tokens."""
    if not resume_tokens or not jd_tokens:
        return 0.0

    resume_doc = nlp(" ".join(resume_tokens))
    jd_doc = nlp(" ".join(jd_tokens))
    similarity = resume_doc.similarity(jd_doc)
    return similarity  # 0–1 range

def section_weighted_score(resume_sections, job_text, keywords):
    total_weighted = 0
    total_weights = 0
    matched_keywords = []
    jd_keywords = []
    missing_keywords = {} # dictionary instead of array

    # array of noun chunks in jd
    #jd_chunks = [chunk.text.strip() for chunk in nlp(job_text).noun_chunks if len(chunk.text.strip()) > 1]
    jd_words = job_text.split()

    #print("***HARD SKILLS***", keywords, "\n***JOB TEXT***", job_text)

    for section, text in resume_sections.items():
        if not text.strip():
            continue

        weight = info_categories.get(section, {"weight": 1})["weight"]

        # direct/exact matches
        jd_keywords.extend([kw for kw in keywords if kw in job_text.lower()])
        matched_keywords.extend([kw for kw in keywords if kw in text.lower() and kw in jd_keywords])

        # split job text into lines
        # for each line, if a missing keyword is found in that line, add context with the keyword
        job_lines = job_text.splitlines()
        for line in job_lines:
            for kw in jd_keywords:
                if kw not in matched_keywords and kw in line:
                    for word in jd_words:
                        if kw in word:
                            i = jd_words.index(word)
                            context_before = ""
                            context_after = ""
                            if i >= 3: context_before = " ".join([jd_words[i-3], jd_words[i-2], jd_words[i-1]])
                            elif i >= 2: context_before = " ".join([jd_words[i-2], jd_words[i-1]])
                            elif i >= 1: context_before = jd_words[i-1]
                            if i < len(jd_words) - 3: context_after = " ".join([jd_words[i+1], jd_words[i+2], jd_words[i+3]])
                            elif i < len(jd_words) - 2: context_after = " ".join([jd_words[i+1], jd_words[i+2]])
                            elif i < len(jd_words) - 1: context_after = jd_words[i+1]
                            missing_keywords.update({kw : [context_before, context_after]}) # keyword, context

        # for words in jd but not in matched, add to missing, then pair with word chunks surrounding that missing keyword
        #print("***SECTION:***", section, "\n***TEXT:***", text)

        # Section contribution (density of matched skills with weights attached)
        # matched skills contribution should be calculated by taking resume skills as a percentage of jd skills.
        jd_keywords = list(set(jd_keywords)) # remove dupes
        matched_keywords = list(set(matched_keywords))

        section_score = weight * (min(len(matched_keywords) / max(len(jd_keywords), 1), 1.0))

        total_weighted += section_score
        total_weights += weight

    avg_score = total_weighted / max(total_weights, 1)
    density = len(matched_keywords) / max(len(jd_keywords), 1)
    matched_keywords = sorted(list(set(matched_keywords))) # sort and remove duplicates
    jd_keywords = sorted(list(set(jd_keywords)))
    #missing_keywords = sorted(set(jd_keywords) - set(matched_keywords))

    return avg_score, density, matched_keywords, missing_keywords

def get_weighted_score(resume_text: str, job_text: str, category: str):

    keywords = get_keywords_list(category)
    resume_sections = segment_sections(resume_text)

    # section score = skill match between resume and JD
    # takes into account four main sections: experience (wgt: 3), education (wgt: 2), skills (wgt: 4), others (wgt: 1)
    # for each section: compare the proportion of matched keywords between resume and JD, then add to the score with weight assigned
    # density returned refers to the total keywords matched in proportion to total JD keywords (for indicative purposes)
    section_score, density, matched_keywords, missing_keywords = section_weighted_score(resume_sections, job_text, keywords)

    # semantic score = use spacy to match noun chunks
    # compare similarities in basic semantics (nouns, verbs, adjs)
    resume_tokens = extract_keywords(resume_text)
    jd_tokens = extract_keywords(job_text)
    semantic_score = semantic_match_score(resume_tokens, jd_tokens)

    # calculate final score: 80% section score, 20% semantics
    final_score = 0.8 * section_score + 0.2 * semantic_score

    # normalize: floor at 25, cap at 95 (don't know if this needed)
    normalised_score = np.clip(25 + final_score * 75, 0, 100)

    #print("section score:", section_score,
    #      "density:", density,
    #      "semantic_score:", semantic_score,
    #      "matched keywords:", matched_keywords,
    #      "missing keywords:", missing_keywords)

    return (round(normalised_score),
            round(section_score*100,2),
            round(density*100,2),
            matched_keywords,
            missing_keywords,
            round(semantic_score * 100,2))
