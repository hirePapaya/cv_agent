import logging

from langgraph.graph import StateGraph, END

from .states import CVAgentState, ChatState
from .nodes import chat_node, close_chat_node, job_posting_node, profile_node, run_enhance_node

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

cv_enhance_graph = StateGraph(state_schema=CVAgentState)
cv_enhance_graph.set_entry_point("job_posting")
cv_enhance_graph.add_node("job_posting", job_posting_node)
cv_enhance_graph.add_node("profile", profile_node)
cv_enhance_graph.add_edge("job_posting", "profile")
cv_enhance_graph.set_finish_point("profile")
agent = cv_enhance_graph.compile()


def route_after_chat(state: ChatState) -> str:
    """Once the job posting has enough info, run the CV enhancement; otherwise
    end the turn so the user can answer the follow-up question."""
    return "run_enhance" if state.get("ready") else END


chat_graph = StateGraph(state_schema=ChatState)
chat_graph.set_entry_point("chat")
chat_graph.add_node("chat", chat_node)
chat_graph.add_node("run_enhance", run_enhance_node)
chat_graph.add_node("close_chat", close_chat_node)
chat_graph.add_conditional_edges("chat", route_after_chat)
chat_graph.add_edge("run_enhance", "close_chat")
chat_graph.set_finish_point("close_chat")
chat_agent = chat_graph.compile()