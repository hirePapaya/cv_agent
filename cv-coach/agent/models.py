from pydantic import BaseModel
from datetime import date

## Job Posting schema

class JobPosting(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    description: str
    requirements: list[str] = []
    nice_to_have: list[str] = []
    keywords: list[str] = []


class JobPostingDraft(BaseModel):
    """Incremental job posting info gathered from the chat, plus the agent's reply."""
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    requirements: list[str] = []
    nice_to_have: list[str] = []
    keywords: list[str] = []
    ready: bool  # true once title + description are enough to start tailoring the CV
    reply: str   # follow-up question, or a short confirmation once ready


## Curriculum Vitae schema

class ProfileContent(BaseModel):
    text: str

class JobExperience(BaseModel):
    company: str
    title: str
    start_date: date
    end_date: date | None = None      # None = current job
    location: str | None = None
    description: str
    achievements: list[str] = []

class ExperienceContent(BaseModel):
    jobs: list[JobExperience]

class EducationEntry(BaseModel):
    institution: str
    degree: str
    start_date: date
    end_date: date | None = None
    location: str | None = None
    gpa: float | None = None

class EducationContent(BaseModel):
    entries: list[EducationEntry]

class SkillsContent(BaseModel):
    categories: dict[str, list[str]]  # {"languages": ["Python"], "tools": [...]}


class CurriculumVitae(BaseModel):
    profile: ProfileContent
    experience: ExperienceContent
    education: EducationContent
    skills: SkillsContent


SectionContent = ProfileContent | ExperienceContent | EducationContent | SkillsContent