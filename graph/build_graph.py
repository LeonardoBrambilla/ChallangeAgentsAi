from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from graph.nodes import (
    executor_node,
    fallback_web_search_node,
    memory_node,
    planner_node,
    route_after_executor,
    user_node,
)
from graph.state import GraphState


def build_graph():
    """Monta o StateGraph do LangGraph: UserNode -> PlannerNode -> ExecutorNode
    -> (fallback web search se RAG sem contexto) -> MemoryNode -> END."""
    graph = StateGraph(GraphState)

    graph.add_node("user", user_node)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("fallback_web_search", fallback_web_search_node)
    graph.add_node("memory", memory_node)

    graph.set_entry_point("user")
    graph.add_edge("user", "planner")
    graph.add_edge("planner", "executor")
    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {"fallback_web_search": "fallback_web_search", "memory": "memory"},
    )
    graph.add_edge("fallback_web_search", "memory")
    graph.add_edge("memory", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
