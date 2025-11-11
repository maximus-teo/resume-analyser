from fastapi import FastAPI, UploadFile, File, Request, Body, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import tempfile
from .utils import extract_pdf_text, get_weighted_score

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyse", response_class=HTMLResponse)
async def analyse(
    request: Request,
    resume_pdf: UploadFile = File(...),
    jobdesc_pdf: UploadFile = File(...),
    resume_textarea: str = Body(...),
    jobdesc_textarea: str = Body(...),
    jobdesc_category: str = Form(...)
):
    res_file_content = await resume_pdf.read()
    job_file_content = await jobdesc_pdf.read()

    if not jobdesc_category:
        jobdesc_category = "fallback"

    if len(res_file_content) > 0:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_resume:
            tmp_resume.write(res_file_content)
            resume_text = extract_pdf_text(tmp_resume.name)
    else:
        resume_text = resume_textarea

    if len(job_file_content) > 0:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_job:
            tmp_job.write(job_file_content)
            job_text = extract_pdf_text(tmp_job.name)
    else:
        job_text = jobdesc_textarea

    (score, section_score, density, matched_skills, semantic_score) = get_weighted_score(resume_text, job_text, jobdesc_category)
    print(f"Job category: {jobdesc_category}, Score: {score}")

    return templates.TemplateResponse("results.html", {
        "request": request,
        "score": score,
        "section_score": section_score,
        "density": density,
        "matched_skills": matched_skills,
        "semantic_score": semantic_score
    })
