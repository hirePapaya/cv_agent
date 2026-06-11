from pydantic import BaseModel
from datetime import date

## Job Posting schema

class JobPosting(BaseModel):
    title: str
    company: str
    location: str | None = None
    description: str
    requirements: list[str] = []
    keywords: list[str] = []


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