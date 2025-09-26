from fastapi import FastAPI, UploadFile, File, Request, Body, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Union
import tempfile
from .utils import extract_pdf_text, match_score

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request":request})

# receives info from form at index.html
@app.post("/analyse", response_class=HTMLResponse)
async def analyse(
    request: Request,
    resume_pdf: UploadFile = File(...),
    jobdesc_pdf: UploadFile = File(...),
    resume_textarea: str = Body(...),
    jobdesc_textarea: str = Body(...),
    jobdesc_category: str = Form(...)
):
    resume_text = ''
    job_text = ''
    res_file_content = await resume_pdf.read()
    job_file_content = await jobdesc_pdf.read()
    if (jobdesc_category == ''): jobdesc_category = "fallback"

    if (len(res_file_content) > 0):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_resume:
            tmp_resume.write(res_file_content)
            resume_path = tmp_resume.name
            resume_text = extract_pdf_text(resume_path)
    else:
        resume_text = resume_textarea

    if (len(job_file_content) > 0):
        with tempfile.NamedTemporaryFile(delete=False) as tmp_job:
            tmp_job.write(job_file_content)
            job_path = tmp_job.name
            job_text = extract_pdf_text(job_path)
    else:
        job_text = jobdesc_textarea

    (score, bonus,
     matched_rel_h, matched_rel_s, matched_ns,
     missing_rel_h, missing_rel_s, missing_ns) = match_score(resume_text, job_text, jobdesc_category)
    
    print("job category: ", jobdesc_category)

    return templates.TemplateResponse(
        "results.html", 
        {
            "request": request,
            "score": score,
            "bonus": bonus,
            "matched_rel_h": sorted(matched_rel_h),
            "matched_rel_s": sorted(matched_rel_s),
            "matched_ns": sorted(matched_ns),
            "missing_rel_h": sorted(missing_rel_h),
            "missing_rel_s": sorted(missing_rel_s),
            "missing_ns": sorted(missing_ns)
        })