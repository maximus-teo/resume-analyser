# How to use
1. Run `.\venv\Scripts\Activate.ps1` to access virtual environment
2. Make sure required packages are installed:
```
pip install -r requirements.txt
```
3. Run `uvicorn app.main:app --reload` to start Uvicorn ASGI

# Improvements to make
- Create curated dictionaries of relevant terms specific to different job descriptions
- Output results with better-looking HTML