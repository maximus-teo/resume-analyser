from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import tempfile
from .utils import extract_pdf_text, match_score

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request":request})

@app.post("/analyse")
async def analyse(
    resume: UploadFile = File(...),
    jobdesc: UploadFile = File(...)
):
    # temporarily save upload files
    with tempfile.NamedTemporaryFile(delete=False) as tmp_resume:
        tmp_resume.write(await resume.read())
        resume_path = tmp_resume.name
    with tempfile.NamedTemporaryFile(delete=False) as tmp_job:
        tmp_job.write(await jobdesc.read())
        job_path = tmp_job.name

    resume_text = extract_pdf_text(resume_path)
    job_text = extract_pdf_text(job_path)

    score, overlap, missing = match_score(resume_text, job_text)

    return {
        "match_score": score,
        "matched_keywords": list(overlap),
        "missing_keywords": list(missing)
    }