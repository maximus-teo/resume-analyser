import os
import json
from groq import Groq
from src.backend.schemas.analysis import ResumeData, JobDescriptionData
from typing import Optional

class AIService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Warning: GROQ_API_KEY not found in environment variables.")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile" # Using a capable model for extraction

    def extract_resume_data(self, text: str) -> Optional[ResumeData]:
        """Extracts structured data from resume text using Groq."""
        prompt = f"""
        You are an expert Resume Parser. Extract the following information from the resume text provided below.
        Return ONLY valid JSON adhering to this structure:
        {{
            "personal_info": {{ "name": "...", "email": "...", "links": [...] }},
            "skills": [ "...", "..." ],
            "experience": [ {{ "company": "...", "role": "...", "duration": "...", "description": "..." }} ],
            "education": [ {{ "institution": "...", "degree": "...", "date": "..." }} ],
            "projects": [ {{ "name": "...", "tools_used": [...], "date": "...", "summary": "..." }} ],
            "career_gaps": [ {{ "period": "...", "reason_speculated": "..." }} ],
            "summary": "..."
        }}
        
        Resume Text:
        {text[:15000]}  # Truncate to avoid context limit issues if extremely long
        """
        
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = completion.choices[0].message.content
            data = json.loads(content)
            return ResumeData(**data)
        except Exception as e:
            print(f"Error extracting resume data: {e}")
            return None

    def extract_job_description(self, text: str) -> Optional[JobDescriptionData]:
        """Extracts structured data from job description text using Groq."""
        prompt = f"""
        You are an expert HR Specialist. Extract the following information from the Job Description text provided below.
        Return ONLY valid JSON adhering to this structure:
        {{
            "role_title": "...",
            "required_skills": ["..."],
            "nice_to_have_skills": ["..."],
            "experience_level": "...",
            "key_responsibilities": ["..."]
        }}

        Job Description Text:
        {text[:15000]}
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = completion.choices[0].message.content
            data = json.loads(content)
            return JobDescriptionData(**data)
        except Exception as e:
            print(f"Error extracting JD data: {e}")
            return None
            
ai_service = AIService()
