from pdfminer.high_level import extract_text
import spacy
import json
import numpy as np
import re
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
    """Load curated skills JSON based on job category."""
    try:
        skills_path = Path(f"app/assets/keywords_{category}.json")
        with open(skills_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [s.lower() for s in data] # LOWERCASE OR NOT?
    except Exception:
        return []
    
def segment_sections(text: str):
    """Roughly segment text into sections based on common resume/JD headers"""
    sections = {"EXPERIENCE": "", "EDUCATION": "", "SKILLS": "", "OTHER": ""}
    current_section = "OTHER" # by default
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        found = False
        for section, info in info_categories.items():
            # not a cut and dried solution but a line must have <5 words to be a header
            # if the entire line matches any header in info_cat, start new section
            if (len(line.split()) < 5) and any(h in line.lower() for h in info["headers"]):
                current_section = section
                found = True
                break
        if not found:
            if sections[current_section] == "": sections[current_section] = line
            else: sections[current_section] += "%nl%" + line
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
    section_scores = [0.0, 0.0, 0.0, 0.0] # others (1), education (2), experience (3), skills (4)

    matched_keywords = {} # dictionary: keyword, weight
    jd_keywords = {} # dictionary: keyword, weight
    missing_keywords = {} # dictionary: keyword, context

    skills_wgt = info_categories.get("SKILLS", {"weight": 4})["weight"] # fallback weight of 4
    extra_keywords = []

    # always prioritise resume weight classification > fallback weight of 4

    # parsing words - classify as extra keywords not found in keyword database
    for line in job_text.splitlines():
        for word in line.split():
            if sum(1 for char in word if char.isupper()) >= 2 and word not in keywords: # 2 or more uppercase e.g. 'EtherCAT', 'RS-485'
                extra_keywords.append(word.lower())
    print("extra_keywords:",extra_keywords)

    # add all extra_keywords to jd_keywords
    for kw in extra_keywords:
        jd_keywords.update({kw: skills_wgt})

    # add relevant keywords from database to jd_keywords
    for kw in keywords:
        pattern = r"\b" + kw.lower() + r"\b"
        if re.search(pattern, job_text.lower()):
        #if kw in job_text.lower():
            jd_keywords.update({kw: skills_wgt})

    # build matched keywords dictionary
    # add resume weighted keywords to matched_keywords
    for section, res_text in resume_sections.items():
        if not res_text.strip():
            continue

        weight = info_categories.get(section, {"weight": 1})["weight"] # fallback weight of 1

        # cross reference database keywords with resume text and job text
        for kw in keywords:
            pattern = r"\b" + kw.lower() + r"\b" # add boundaries to find whole word
            if re.search(pattern, res_text.lower()) and re.search(pattern, job_text.lower()) and kw not in matched_keywords: # ensure weight is not overridden
            #if kw.lower() in res_text.lower() and kw.lower() in job_text.lower() and kw not in matched_keywords: # ensure weight is not overridden
                matched_keywords.update({kw: weight})
                jd_keywords.update({kw: weight}) # ensure jd_keywords has accurate weights
        if extra_keywords:
            for kw in extra_keywords:
                pattern = r"\b" + kw.lower() + r"\b"
                if re.search(pattern, res_text.lower()) and kw not in matched_keywords:
                #if kw in res_text.lower() and kw not in matched_keywords:
                    matched_keywords.update({kw: skills_wgt})

    # build missing keywords dictionary
    # extract context for each missing keyword
    jobtext = []
    for line in job_text.splitlines():
        jobtext.extend([word for word in line.split()])
    print("jobtext:",jobtext)

    for kw, wgt in jd_keywords.items():
        if kw not in matched_keywords:
            context_before = ""
            context_after = ""
            missing_keywords.update({kw : [context_before, context_after]})
            length = len(kw.split())
            if length == 1:
                for word in jobtext:
                    i = jobtext.index(word)
                    if i >= 3: context_before = " ".join([jobtext[i-3], jobtext[i-2], jobtext[i-1]])
                    elif i >= 2: context_before = " ".join([jobtext[i-2], jobtext[i-1]])
                    elif i >= 1: context_before = jobtext[i-1]
                    if i < len(jobtext) - 3: context_after = " ".join([jobtext[i+1], jobtext[i+2], jobtext[i+3]])
                    elif i < len(jobtext) - 2: context_after = " ".join([jobtext[i+1], jobtext[i+2]])
                    elif i < len(jobtext) - 1: context_after = jobtext[i+1]

                    pattern = r"\b" + kw.lower() + r"\b"
                    if kw not in matched_keywords and re.search(pattern, word.lower()):
                        missing_keywords.update({kw : [context_before, context_after]})
            elif length > 1:
                # find location of kw in jobtext array
                print("multi word kw detected:", kw)
                i = -1
                for word in jobtext:
                    i = jobtext.index(word)
                    if i < len(jobtext) - (length-1):
                        match = False
                        for k in range(0,length): # e.g. if kw has 2 words, k iterates thru 0 and 1.
                            match = re.sub(r'[^a-zA-Z0-9 ]', '', jobtext[i+k]) == kw.split()[k]
                        if match:
                            k = i+1
                            while k < len(jobtext):
                                concat = re.sub(r'[^a-zA-Z0-9 ]', '', " ".join([word, jobtext[k]]))
                                print("concat:",concat)
                                if concat == kw and i >= 0: 
                                    print("kw passed i >= 0:",kw)
                                    if i >= 3: context_before = " ".join([jobtext[i-3], jobtext[i-2], jobtext[i-1]])
                                    elif i >= 2: context_before = " ".join([jobtext[i-2], jobtext[i-1]])
                                    elif i >= 1: context_before = jobtext[i-1]
                                    if i < len(jobtext) - 3: context_after = " ".join([jobtext[i+length], jobtext[i+length+1], jobtext[i+length+2]])
                                    elif i < len(jobtext) - 2: context_after = " ".join([jobtext[i+length], jobtext[i+length+1]])
                                    elif i < len(jobtext) - 1: context_after = jobtext[i+length]
                                    
                                    missing_keywords.update({kw : [context_before, context_after]})
                                    break
                                elif concat not in kw:
                                    i = -1
                                    break
                                k = k + 1
            
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
    print("jd_keywords:",jd_keywords)
    print("matched_keywords:", matched_keywords)
    print("missing_keywords:", missing_keywords)
    print("keyword score:",resume_weight,"/",jd_weight)
    print(section_scores)

    return avg_score, section_scores, density, matched_keywords, missing_keywords

def get_weighted_score(resume_text: str, job_text: str, category: str):

    keywords = get_keywords_list(category)
    resume_sections = segment_sections(resume_text)

    # keyword score = WEIGHTED keyword match between resume and JD
    # takes into account four main sections: experience (wgt: 3), education (wgt: 2), skills (wgt: 4), others (wgt: 1)
    # for each section: compare the proportion of matched keywords between resume and JD, then add to the score with weight assigned
    # density returned refers to the total keywords matched in proportion to total JD keywords (for indicative purposes)
    keyword_score, section_scores, density, matched_keywords, missing_keywords = section_weighted_score(resume_sections, job_text, keywords)

    # semantic score = use spacy to match noun chunks
    # compare similarities in basic semantics (nouns, verbs, adjs)
    resume_tokens = extract_keywords(resume_text)
    jd_tokens = extract_keywords(job_text)
    semantic_score = semantic_match_score(resume_tokens, jd_tokens)

    # calculate final score: 80% keyword score, 20% semantics
    final_score = 0.8 * keyword_score + 0.2 * semantic_score

    # normalize: floor at 25, cap at 95 (don't know if this needed)
    # normalised_score = np.clip(25 + final_score * 75, 0, 100)
    
    resume_sections = {
        section: text.split("%nl%")
        for section, text in resume_sections.items()
        }

    return (round(final_score*100,2),
            round(keyword_score*100,2),
            resume_sections,
            section_scores,
            round(density*100,2),
            matched_keywords,
            missing_keywords,
            round(semantic_score * 100,2))
