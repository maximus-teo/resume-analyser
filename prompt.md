## Role & Goal
**Act as**: A Senior Full-Stack Engineer and Lead UX Designer.
**Mission**: Revamp the Resume Analyser from a prototype to a production-ready, AI-powered application with a high-end UI.

## Context (The "Before")
**Current State**: The project is currently barebones with spaCy natural language processing, such as parsing tokens and noun chunks.

**Tech Stack**: Python, FastAPI, basic HTML, CSS, JSON files for keywords, no database

**Current Logic**: It uses regex and simple keyword matching which is brittle and inaccurate.

**Known Issues**:
- User is responsible for choosing a resume category before analysis but user's judgment may not be accurate
- Algorithm is not fool-proof, as it cannot correctly identify which terms are relevant or considered important for scoring
- Matched keywords can't always parse and match multiple word terms properly
- Missing keywords ("Try adding these keywords" section) doesn't always correctly show the context before and after the keyword 
- UI is not mobile-responsive
- UI is basic, utilising the default form appearance

## The Vision (The "After")
**Core Logic Upgrade**: Replace basic parsing with an AI-driven engine. I want to use Groq API to extract structured data (Skills, Experience, Career Gaps) - I have an API key already included in my .env file with the variable declared as "GROQ_API_KEY". You don't have to view my .env file for security purposes, make sure it remains secure and just use the variable.

**UI/UX Aesthetic**:
- The "vibe" should be modern minimalist SaaS, light mode, linear-style interface. Focus on clean typography, consistent padding, and subtle animations.
- Specifically, mimic the "Glassmorphism" effect and the progress bar style.

**Key New/Revamped Features**:

1. Landing page: 
- PDF and raw text formats should be accepted for both job description and resume.
- Drag-and-drop file upload zone for job description and resume. 

2. Results page:
- Screen to display all three components: resume in simple markdown format, job description and results panel containing the "match score", matched terms and missing terms (more details listed next)
- A "Match Score" gauge out of 100% based on the provided job description and resume, should be an accurate measure of how likely the resume can pass an Automated Tracking System (ATS) resume checker
- A list of matched terms, ranked from highest impact on match score to lowest impact (color-coded gradient)
- Similarly, a list of missing terms also ranked from highest impact on matched score to lowest impact (same color coding)
- Each matched term and missing term is clickable, and will highlight the location of that term wherever present, on the resume *and/or* the job description

## The Strategy (The "Bridge")
Do not rewrite the whole app in one go. Please follow this phased approach:

**Phase 1 (Discovery)**: Scan my existing directory. Identify redundant files and suggest a modern, modular folder structure (e.g., /src/backend, /src/frontend, /tests).

**Phase 2 (Core Logic)**: Implement the AI analysis service as a standalone module.

**Phase 3 (UI Revamp)**: Apply Tailwind CSS components to replace the current styling.

## Operational Rules (Anti-Vibe-Coding)
To ensure the code remains professional and maintainable:

**No Inline Styles**: Use Tailwind classes exclusively.

**Type Safety**: Use Type Hints in Python and JSDoc/Typescript for JS.

**Error Handling**: Every API call must have a try/catch block and user-facing error messages.

**Documentation**: Add docstrings to all new functions.

**Environment Variables**: Never hardcode API keys; follow the pre-existing .env file.

## Next Step
Before writing any code, generate a Technical Design Document (Artifact) outlining your proposed file structure and the schema for the AI's JSON output. Wait for my green light before proceeding.