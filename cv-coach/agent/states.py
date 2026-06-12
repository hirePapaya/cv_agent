from typing import TypedDict, Annotated, Union
from operator import add
from .models import SectionContent, JobPosting



class SectionState(TypedDict):
    """Represents the state of a single CV section (e.g., experience, education)."""
    name: str                  # "experience", "education", "skills"...
    original_content: Union[SectionContent, None]  # as extracted from the CV (may be unstructured)
    current_content: Union[SectionContent, None]
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
    job_description: str | None          # raw job posting text, as provided by the user
    job_posting: JobPosting | None      # parsed job posting information
    messages: Annotated[list, add]       # conversation history for interrupts
    final_cv: str | None



class ChatState(TypedDict):
    """State for the chat with the user, focused on a single instruction and its resulting edit operations."""
    message: str               # the user's latest message (instruction or answer)
    history: list[dict]        # recent chat turns: {"role": "user" | "agent", "text": str}
    instruction: str           # the user's latest editing instruction
    job_posting: dict | None   # job posting info gathered from the chat so far
    ready: bool                # true once job_posting has enough info to run the CV enhancement
    reply: str                 # short conversational reply to show the user
    log: list[str]             # past-tense, concrete change notes
    ops: list[dict]            # edit operations to apply to the CV