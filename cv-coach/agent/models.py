from pydantic import BaseModel
from datetime import date

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

class EducationContent(BaseModel):
    entries: list[EducationEntry]

class SkillsContent(BaseModel):
    categories: dict[str, list[str]]  # {"languages": ["Python"], "tools": [...]}

SectionContent = ProfileContent | ExperienceContent | EducationContent | SkillsContent