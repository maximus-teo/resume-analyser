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

def extract_pdf_text(file_path: str):
    return extract_text(file_path)

def preprocess_text(text: str):
    return "".join(text.lower())

def get_keywords_list(category: str):
    """Load curated skills JSON based on job category. Makes all strings lowercase."""
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

def section_weighted_score(resume_sections, job_text, keywords): # NOTE: keywords are already lowercase
    resume_weight = 0
    jd_weight = 0
    matched_keywords = {} # dictionary: keyword, weight
    jd_keywords = {} # dictionary: keyword, weight
    missing_keywords = {} # dictionary instead of array

    # categorise JD into the same four categories to calculate its total score.
    # not accurate to categorise JD keywords based on the fact that they share the same line as a header keyword.
    #for line in job_text.lower().splitlines():
    #    for cat_name, cat_data in info_categories.items():
    #        wgt = cat_data["weight"]
    #        for header in cat_data["headers"]:
    #            if header in line: 
    #                for kw in keywords:
    #                    if kw in line.lower():
    #                        jd_keywords.update({kw: wgt})
    #                        jd_weight += wgt
    
    # array of noun chunks in jd
    #jd_chunks = [chunk.text.strip() for chunk in nlp(job_text).noun_chunks if len(chunk.text.strip()) > 1]
    #jd_keywords.extend([kw for kw in keywords if kw in job_text.lower()])
    #print("***HARD SKILLS***", keywords, "\n***JOB TEXT***", job_text)

    # format for resume sections is "HEADER": "TEXT"
    for section, text in resume_sections.items():
        if not text.strip():
            continue

        weight = info_categories.get(section, {"weight": 1})["weight"] # fallback weight of 1

        # direct/exact matches
        num_matches = 0
        for kw in keywords:
            if kw in text.lower() and kw in job_text.lower() and kw not in matched_keywords:
                matched_keywords.update({kw: weight})
                num_matches += 1
        #matched_keywords.extend([kw for kw in keywords if kw in text.lower() and kw in job_text.lower()])
        #matched_keywords = list(set(matched_keywords))
        #num_matches = len(matched_keywords) - num_matches

        #jd_keywords.extend([kw for kw in keywords if kw in job_text.lower()])

        # for words in jd but not in matched, add to missing, then pair with word chunks surrounding that missing keyword
        #print("***SECTION:***", section, "\n***TEXT:***", text)

        # Section contribution (density of matched skills with weights attached)
        # matched skills contribution should be calculated by taking resume skills as a percentage of jd skills.
        # keyword_score = weight * (min(len(matched_keywords) / max(len(jd_keywords), 1), 1.0))

        resume_weight += weight * num_matches

    # then add missing keywords to jd_keywords and classify them by adding skills weight to them (since most likely to be a skill) - not a cut and dried solution
    skills_wgt = info_categories.get("SKILLS", {"weight": 4})["weight"] # fallback weight of 4
    for kw, wgt in matched_keywords.items():
        if kw not in jd_keywords:
            jd_keywords.update({kw: wgt})

    for kw in keywords:
        if kw not in jd_keywords and kw in job_text.lower():
            jd_keywords.update({kw: skills_wgt})

    # split job text into lines
    # for each line, if a missing keyword is found in that line, add context with the keyword
    # do we want to add a criteria to recognise any string with 2 or more uppercase characters as an important keyword? - indicate as 'might be important'
    for line in job_text.splitlines():
        for kw in jd_keywords:
            if kw not in matched_keywords and kw in line:
                words = line.split()
                for word in words:
                    if kw in word:
                        i = words.index(word)
                        context_before = ""
                        context_after = ""
                        if i >= 3: context_before = " ".join([words[i-3], words[i-2], words[i-1]])
                        elif i >= 2: context_before = " ".join([words[i-2], words[i-1]])
                        elif i >= 1: context_before = words[i-1]
                        if i < len(words) - 3: context_after = " ".join([words[i+1], words[i+2], words[i+3]])
                        elif i < len(words) - 2: context_after = " ".join([words[i+1], words[i+2]])
                        elif i < len(words) - 1: context_after = words[i+1]
                        missing_keywords.update({kw : [context_before, context_after]}) # keyword, context

    for kw, wgt in jd_keywords.items():
        jd_weight += wgt

    avg_score = resume_weight / max(jd_weight, 1)
    density = len(matched_keywords) / max(len(jd_keywords), 1)
    #matched_keywords = sorted(list(set(matched_keywords))) # sort and remove duplicates
    print("jd_keywords:",jd_keywords) # how to sort keys?
    print("matched_keywords:", matched_keywords)
    print("keyword score:",resume_weight,"/",jd_weight)
    #jd_keywords = sorted(list(set(jd_keywords)))
    #missing_keywords = sorted(set(jd_keywords) - set(matched_keywords))

    return avg_score, density, matched_keywords, missing_keywords

def get_weighted_score(resume_text: str, job_text: str, category: str):

    keywords = get_keywords_list(category)
    resume_sections = segment_sections(resume_text)

    # keyword score = skill match between resume and JD
    # takes into account four main sections: experience (wgt: 3), education (wgt: 2), skills (wgt: 4), others (wgt: 1)
    # for each section: compare the proportion of matched keywords between resume and JD, then add to the score with weight assigned
    # density returned refers to the total keywords matched in proportion to total JD keywords (for indicative purposes)
    keyword_score, density, matched_keywords, missing_keywords = section_weighted_score(resume_sections, job_text, keywords)

    # semantic score = use spacy to match noun chunks
    # compare similarities in basic semantics (nouns, verbs, adjs)
    resume_tokens = extract_keywords(resume_text)
    jd_tokens = extract_keywords(job_text)
    semantic_score = semantic_match_score(resume_tokens, jd_tokens)

    # calculate final score: 80% keyword score, 20% semantics
    final_score = 0.8 * keyword_score + 0.2 * semantic_score

    # normalize: floor at 25, cap at 95 (don't know if this needed)
    normalised_score = np.clip(25 + final_score * 75, 0, 100)

    #print("keyword score:", keyword_score,
    #      "density:", density,
    #      "semantic_score:", semantic_score,
    #      "matched keywords:", matched_keywords,
    #      "missing keywords:", missing_keywords)

    return (round(normalised_score),
            round(keyword_score*100,2),
            round(density*100,2),
            matched_keywords,
            missing_keywords,
            round(semantic_score * 100,2))
