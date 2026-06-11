from langgraph.graph import StateGraph

from .states import CVAgentState, CVEditState
from .nodes import cv_editor_node, job_posting_node


job_posting_graph = StateGraph(state_schema=CVAgentState)
job_posting_graph.set_entry_point("job_posting")
job_posting_graph.add_node("job_posting", job_posting_node)
job_posting_graph.set_finish_point("job_posting")

agent = job_posting_graph.compile()


cv_editor_graph = StateGraph(state_schema=CVEditState)
cv_editor_graph.set_entry_point("edit")
cv_editor_graph.add_node("edit", cv_editor_node)
cv_editor_graph.set_finish_point("edit")

cv_editor_agent = cv_editor_graph.compile()
