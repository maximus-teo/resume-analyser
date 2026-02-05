from fastapi import FastAPI, UploadFile, File, Request, Body, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

# Import services from new location
from src.backend.services.parser import extract_pdf_text
from src.backend.services.scoring import get_weighted_score
from src.backend.services.ai_service import ai_service

app = FastAPI(title="Resume Analyser")

# Add CORS Middleware to allow requests from any origin (e.g. GitHub Pages, Localhost)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(BASE_DIR, "src", "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "src", "frontend", "static")

templates = Jinja2Templates(directory=TEMPLATE_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyse", response_class=HTMLResponse)
async def analyse(
    request: Request,
    resume_pdf: UploadFile = File(None),
    jobdesc_pdf: UploadFile = File(None),
    resume_textarea: str = Form(None),
    jobdesc_textarea: str = Form(None),
    jobdesc_category: str = Form("fallback")
):
    # Handle Resume Input
    resume_text = ""
    if resume_pdf and resume_pdf.filename:
        res_file_content = await resume_pdf.read()
        if len(res_file_content) > 0:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_resume:
                tmp_resume.write(res_file_content)
                tmp_resume.flush()
                resume_text = extract_pdf_text(tmp_resume.name)
    elif resume_textarea:
        resume_text = resume_textarea

    # Handle Job Description Input
    job_text = ""
    if jobdesc_pdf and jobdesc_pdf.filename:
        job_file_content = await jobdesc_pdf.read()
        if len(job_file_content) > 0:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_job:
                tmp_job.write(job_file_content)
                tmp_job.flush()
                job_text = extract_pdf_text(tmp_job.name)
    elif jobdesc_textarea:
        job_text = jobdesc_textarea

    # if all fields are empty
    if not resume_text and not job_text and not resume_pdf and not jobdesc_pdf:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Please provide both Resume and Job Description."
        })

    # AI Extraction
    # We use the raw text for the legacy scorer for now to ensure continuity, 
    # but we ALSO extract structured data for future display/logic.
    # ideally we merge them. For this step, pass the resume_text to the legacy scorer
    # AND try to get some AI metadata.
    
    # For matching, the legacy scorer works on raw text and keywords.
    # To fully utilize AI, ideally use the AI extracted skills for matching.
    
    # 1. Extract Structured Data
    print("Extracting Resume Data with AI...")
    resume_data = ai_service.extract_resume_data(resume_text)
    print("Extracting JD Data with AI...")
    jd_data = ai_service.extract_job_description(job_text)
    
    # 2. Hybrid Scoring
    # If AI extraction succeeds, inject extracted skills into the scoring algorithm 
    
    resume_skills = resume_data.skills if resume_data else []
    jd_required = jd_data.required_skills if jd_data else []
    jd_nice = jd_data.nice_to_have_skills if jd_data else []
    
    (score, keyword_score, resume_sections, section_scores, density, matched_keywords, missing_keywords, semantic_score) = get_weighted_score(
        resume_text, 
        job_text, 
        jobdesc_category,
        ai_resume_skills=resume_skills,
        ai_jd_required=jd_required,
        ai_jd_nice=jd_nice
    )

    # JSON response
    resume_json = resume_data.model_dump() if resume_data else {}
    print("resume json from ai:", resume_json)
    jd_json = jd_data.model_dump() if jd_data else {}
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "job_category": jobdesc_category,
        "score": score,
        "keyword_score": keyword_score,
        "resume_sections": resume_sections,
        "job_text": job_text,
        "section_scores": section_scores,
        "density": density,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "semantic_score": semantic_score,
        "ai_resume_data": resume_json,
        "ai_jd_data": jd_json
    })
