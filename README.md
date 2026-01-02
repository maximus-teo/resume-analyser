# Resume Analyser

This Python tool helps you find key similarities and differences between your resume and a job listing. Simply upload your resume and the job description (certain instructions to follow) and receive a match score out of 100%. 

## What is an ATS?

Companies often use an ATS to automatically screen, sort and rank potential candidates by scanning all resumes for relevant keywords and required qualifications for an advertised position, before deeming them appropriate for human review. To boost your chances of passing through the ATS, you can ensure that your resume uses clean formatting, standard headings and includes keywords in verbatim from the job description, so that it is easily readable by the ATS to reach a hiring manager. The higher the match score is out of 100, the more likely the resume will pass through the ATS.

# Tips for best results

- Upload your resume as a PDF, or raw text is accepted
- Upload only the Requirements/Qualifications/Skills section of the job listing
- Do not upload any other info such as company history or benefits/perks
- Select the job category that best fits the job listing

# Note

- This resume analyser searches for keywords and phrases, not entire sentences
- Match score is based on number of overlaps between the resume and job listing
- Bonus points are given if select keywords are found in the resume, job listing and the curated dictionary

# How it works

## 1. Extract
Retrieve all raw text from the resume and job description (JD).

## 2. Build 'matched' dictionary
Cross-reference all database keywords with both resume and JD, adding all common keywords to a 'matched' keyword dictionary.

## 3. Build 'jd' dictionary
Cross-reference all database keywords with JD itself, adding all common keywords to a 'jd' keyword dictionary.

## 4. Find extra keywords
Scan the JD for important technical terms - these are unique keywords that are not found in our existing database - and add them to the 'jd' dictionary.

## 5. Build 'missing' dictionary
Compare 'matched' and 'jd' dictionaries, filtering out keywords to add to a 'missing' dictionary - these are keywords only found in the JD but not the resume.

## 6. Calculate match score
The match score has a weight distribution of 80% keywords, 20% semantics (using NLP by spaCy). The keywords scoring algorithm is done by partitioning the resume into four sections (skills, experience, education and others) with descending weights respectively. Each matched keyword in the resume and JD receives its respective weight based on the section it is found in, and the total weights are tallied up. The final percentage is calculated by taking the total resume weight divided by the total JD weight.

# How to use

1. Clone this repository
   ```
   git clone https://github.com/maximus-teo/resume-analyser.git
   ```
2. Start by creating a virtual environment (`venv`) with
   ```
   python -m venv venv
   ```
3. Access the virtual environment
   ```
   .\venv\Scripts\Activate.ps1
   ```
   If needed, execute the command `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` to allow running scripts on your system.
4. Make sure all required packages are installed. This will take a few minutes to complete.
   ```
   pip install -r requirements.txt
   ```
   You may have to manually install the spaCy package:
   ```
   python -m spacy download en_core_web_md
   ```
5. Reload Uvicorn ASGI
   ```
   uvicorn app.main:app --reload
   ```
6. Go to `https://127.0.0.1:8000/` to test
