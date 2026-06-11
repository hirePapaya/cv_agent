from typing import TypedDict
from langgraph.graph import StateGraph


class AgentState(TypedDict):
    message: str


def greeting_node(state: AgentState) -> AgentState:
    """A simple node that generates a greeting message."""
    print("Greeting node invoked with message:", state["message"])
    return AgentState(message="Hello, I'm your CV coach!")


def second_node(state: AgentState) -> AgentState:
    """A simple node that generates a greeting message."""
    print("Second node invoked with message:", state["message"])
    return AgentState(message="Hello, I'm your CV coach!")


state_graph = StateGraph(state_schema=AgentState)
state_graph.set_entry_point("greeting")
state_graph.add_node("greeting", greeting_node)
state_graph.add_edge("greeting", "second")
state_graph.add_node("second", second_node)
state_graph.set_finish_point("second")

agent = state_graph.compile()
