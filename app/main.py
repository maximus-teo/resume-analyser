from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import tempfile
from .utils import extract_pdf_text, match_score

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request":request})

@app.post("/analyse", response_class=HTMLResponse)
async def analyse(
    request: Request,
    resume: UploadFile = File(...),
    jobdesc: UploadFile = File(...)
):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_resume:
        tmp_resume.write(await resume.read())
        resume_path = tmp_resume.name
    with tempfile.NamedTemporaryFile(delete=False) as tmp_job:
        tmp_job.write(await jobdesc.read())
        job_path = tmp_job.name

    resume_text = extract_pdf_text(resume_path)
    job_text = extract_pdf_text(job_path)

    score, overlap, missing = match_score(resume_text, job_text)

    return templates.TemplateResponse(
        "results.html", 
        {
            "request": request,
            "score": score,
            "matched": sorted(overlap),
            "missing": sorted(missing)
        })