# Resume Analyser
This Python tool helps you find key similarities and differences between your resume and a job listing. Simply upload your resume and the job description (certain instructions to follow) and receive a match score out of 100%.

# Tips for best results
- Upload your resume as a PDF, but raw text is accepted
- Upload only the Requirements/Qualifications/Skills section of the job listing
- Do not upload any other info such as company history or benefits/perks
- Select the job category that best fits the job listing

# Note
- This resume analyser searches for keywords and phrases, not entire sentences
- Match score is based on number of overlaps between the resume and job listing
- Bonus points are given if select keywords are found in the resume, job listing and the curated dictionary

# How to use
1. Start by creating a virtual environment (`venv`) with
    ```
    python -m venv venv
    ```
2. Access the virtual environment
    ```
    .\venv\Scripts\Activate.ps1
    ```
3. Make sure all required packages are installed
    ```
    pip install -r requirements.txt
    ```
4. Reload Uvicorn ASGI
    ```
    uvicorn app.main:app --reload
    ```
5. Go to `https://127.0.0.1:8000/` to test