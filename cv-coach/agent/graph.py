import logging

from langgraph.graph import StateGraph

from .states import CVAgentState, ChatState
from .nodes import (
    chat_node,
    education_node,
    experience_node,
    general_check_node,
    job_posting_node,
    profile_node,
    skills_node,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def finish_node(_state: CVAgentState) -> dict:
    """Fan-in node: reached once all parallel section nodes complete."""
    logger.info("cv_enhance_graph: all sections complete")
    return {}


# CV enhancement graph
# job_posting → [profile, experience, education, skills] (parallel) → finish
cv_enhance_graph = StateGraph(state_schema=CVAgentState)
cv_enhance_graph.set_entry_point("job_posting")
cv_enhance_graph.add_node("job_posting", job_posting_node)
cv_enhance_graph.add_node("profile", profile_node)
cv_enhance_graph.add_node("experience", experience_node)
cv_enhance_graph.add_node("education", education_node)
cv_enhance_graph.add_node("skills", skills_node)
cv_enhance_graph.add_node("general_check", general_check_node)
cv_enhance_graph.add_node("finish", finish_node)

# Fan-out: job_posting triggers all section nodes in parallel
cv_enhance_graph.add_edge("job_posting", "profile")
cv_enhance_graph.add_edge("job_posting", "experience")
cv_enhance_graph.add_edge("job_posting", "education")
cv_enhance_graph.add_edge("job_posting", "skills")

# Fan-in: all section nodes converge on general_check once all complete
cv_enhance_graph.add_edge("profile", "general_check")
cv_enhance_graph.add_edge("experience", "general_check")
cv_enhance_graph.add_edge("education", "general_check")
cv_enhance_graph.add_edge("skills", "general_check")

cv_enhance_graph.add_edge("general_check", "finish")
cv_enhance_graph.set_finish_point("finish")
agent = cv_enhance_graph.compile()

# Chat graph: gathers job posting info from the user (one turn at a time)
chat_graph = StateGraph(state_schema=ChatState)
chat_graph.set_entry_point("chat")
chat_graph.add_node("chat", chat_node)
chat_graph.set_finish_point("chat")
chat_agent = chat_graph.compile()
