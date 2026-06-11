from states import CVAgentState, SectionState
from models import CurriculumVitae, SectionContent, ProfileContent, ExperienceContent, EducationContent, SkillsContent


def read_raw_cv() -> CurriculumVitae:
    return CurriculumVitae(
        profile=ProfileContent(text="John Doe"),
        experience=ExperienceContent(jobs=[]),
        education=EducationContent(entries=[]),
        skills=SkillsContent(categories={})
    )


def process_input(raw_cv: str) -> CVAgentState:
    # Placeholder: In a real implementation, you'd parse the CV into sections and content.
    # For now, we just create a dummy state with one section.
    return CVAgentState(
        raw_cv=raw_cv,
        sections={
            "experience": SectionState(
                name="experience",
                original_content=SectionContent(text=raw_cv),  # In reality, this would be structured data
                current_content=SectionContent(text=raw_cv),
                score=None,
                score_threshold=0.7,
                evaluation_notes="",
                update_plan=None,
                questions=[],
                user_answers={},
                status="pending",
                revision_count=0
            )
        },
        current_section="experience",
        section_order=["experience"],
        user_profile={},
        target_role=None,
        job_description=None,
        messages=[],
        final_cv=None
    )

