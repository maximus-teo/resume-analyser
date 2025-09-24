# How to use
1. Start by creating a virtual environment (`venv`) with `python -m venv venv`
2. Run `.\venv\Scripts\Activate.ps1` to access `venv`
3. Make sure required packages are installed:
    ```
    pip install -r requirements.txt
    ```
4. Run `uvicorn app.main:app --reload` to start Uvicorn ASGI
5. Go to `https://127.0.0.1:8000/` to test

# Improvements to make
- Create curated dictionaries of relevant terms specific to different job descriptions
- Output results with better-looking HTML

# Main idea
- A resume and a job description are provided
- Break the resume and job description down into their keywords
- Identify 1-2 fields that fit the job description (e.g. engineering and science)
- Match between both and find the percentage of matched keywords over total keywords
- Give extra points for soft skills and even more points for matching technical skills (weighted accordingly)
- List the matched words and missing words