from pydantic import BaseModel, Field
from typing import List, Optional

class PersonalInfo(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: Optional[str] = Field(description="Email address")
    links: List[str] = Field(default_factory=list, description="URLs to LinkedIn, Portfolio, etc.")

class ExperienceItem(BaseModel):
    company: str = Field(description="Company name")
    role: str = Field(description="Job title")
    duration: str = Field(description="Time period of employment")
    description: str = Field(description="Brief summary of responsibilities and achievements")

class EducationItem(BaseModel):
    institution: str = Field(description="University or School name")
    degree: str = Field(description="Degree or Certificate obtained")
    date: str = Field(description="Month and year of graduation or completion")

class ProjectItem(BaseModel):
    name: str = Field(description="Name of the project")
    tools_used: List[str] = Field(default_factory=list, description="Names of tools and technologies used like Python, Excel, etc.")
    date: str = Field(description="Month and year, or duration of the project")
    summary: str = Field(description="Brief description of the project")

class CareerGap(BaseModel):
    period: str = Field(description="Time period of the gap")
    reason_speculated: str = Field(description="Potential reason or context for the gap based on surrounding info")

class ResumeData(BaseModel):
    personal_info: PersonalInfo
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list, description="List of projects found in the resume")
    career_gaps: List[CareerGap] = Field(default_factory=list)
    summary: str = Field(description="Brief professional summary extracted from the resume")

class JobDescriptionData(BaseModel):
    role_title: str = Field(description="Title of the job role")
    required_skills: List[str] = Field(default_factory=list, description="Mandatory skills required for the job")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Optional or preferred skills")
    experience_level: str = Field(description="Required experience level (e.g., Senior, Junior, 3+ years)")
    key_responsibilities: List[str] = Field(default_factory=list, description="Main responsibilities of the role")
