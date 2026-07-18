from typing import Any, List, TypedDict


class LogEntry(TypedDict):
    node: str
    message: str


class GraphState(TypedDict, total=False):
    question: str
    route: str
    answer: str
    has_context: bool
    logs: List[LogEntry]
    history: List[dict[str, Any]]
