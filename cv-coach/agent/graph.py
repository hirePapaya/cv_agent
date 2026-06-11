from langgraph.graph import StateGraph

from .states import CVAgentState, CVEditState
from .nodes import cv_editor_node, job_posting_node, welcome_node



def call_child_cv_adapter(state: CVEditState) -> CVAgentState:
    result = cv_adapter_graph.invoke(CVAgentState)
    return {"messages": result["messages"]}

 

cv_adapter_graph = StateGraph(state_schema=CVAgentState)
cv_adapter_graph.set_entry_point("job_posting")
cv_adapter_graph.add_node("job_posting", job_posting_node)
cv_adapter_graph.set_finish_point("job_posting")
cv_adapter_agent = cv_adapter_graph.compile()


cv_editor_graph = StateGraph(state_schema=CVEditState)
cv_editor_graph.set_entry_point("edit")
cv_editor_graph.add_node("welcome", welcome_node)
cv_editor_graph.add_node("cv_adapter_graph", call_child_cv_adapter)
cv_editor_graph.add_edge("welcome", "cv_adapter_graph")
cv_editor_graph.add_node("editor", cv_editor_node)
cv_editor_graph.add_edge("cv_adapter_graph", "editor")
cv_editor_graph.set_finish_point("editor")
cv_editor_agent = cv_editor_graph.compile()