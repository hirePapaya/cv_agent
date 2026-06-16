from google import genai
from google.genai import types

from ..models import JobPosting
from ..states import CVAgentState

def parse_job_posting(raw_text: str) -> JobPosting:
    """Parse a raw job posting string into a structured JobPosting."""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction="Extract structured information from the job posting. Only use information present in the text.",
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=JobPosting,
        ),
    )
    if response.parsed is None:
        raise ValueError(f"Failed to parse job posting: {response.text}")
    return response.parsed



def job_posting_node(state: CVAgentState) -> CVAgentState:
    """LangGraph node: parses the raw job description into state."""
    raw = state.get("job_description")
    if not raw:
        return state   
    job_posting = parse_job_posting(raw)
    return {
        **state,
        "job_posting": job_posting.model_dump(), 
        "target_role": job_posting.title,
    }

