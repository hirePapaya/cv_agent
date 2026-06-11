from typing import TypedDict, Annotated
from operator import add

class SectionState(TypedDict):
    """Represents the state of a single CV section (e.g., experience, education)."""
    name: str                  # "experience", "education", "skills"...
    original_content: str
    current_content: str       # evolves as you update
    score: float | None
    score_threshold: float     # what counts as "good enough"
    evaluation_notes: str      # why it scored that way
    update_plan: str | None
    questions: list[str]       # questions for the user
    user_answers: dict         # answers collected
    status: str                # "pending" | "needs_input" | "approved" | "done"
    revision_count: int        # avoid infinite improve loops



class CVAgentState(TypedDict):
    """Represents the overall state of the CV coaching process."""
    raw_cv: str                          # original document
    sections: dict[str, SectionState]    # all sections
    current_section: str                 # which one is being processed
    section_order: list[str]             # processing queue
    user_profile: dict                   # accumulated info from answers (reusable across sections!)
    target_role: str | None              # tailoring the CV toward a job?
    job_description: str | None
    messages: Annotated[list, add]       # conversation history for interrupts
    final_cv: str | None