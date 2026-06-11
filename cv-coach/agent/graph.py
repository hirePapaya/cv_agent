from langgraph.graph import StateGraph

from .states import CVAgentState
from .nodes import job_posting_node


state_graph = StateGraph(state_schema=CVAgentState)
state_graph.set_entry_point("job_posting")
state_graph.add_node("job_posting", job_posting_node)
state_graph.set_finish_point("job_posting")

agent = state_graph.compile()
