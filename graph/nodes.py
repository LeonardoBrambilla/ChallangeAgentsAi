from agents.planner_agent import ROUTE_RAG, decide_route
from agents.rag_agent import run_rag_agent
from agents.sql_agent import run_sql_agent
from agents.weather_agent import run_weather_agent
from agents.web_search_agent import run_web_search_agent
from graph.state import GraphState
from logging_config import configure_logging, log_event
from settings import settings

logger = configure_logging(settings.log_level)


def _append_log(logs: list, node: str, message: str) -> list:
    logs = list(logs)
    logs.append({"node": node, "message": message})
    log_event(logger, "graph_node", node=node, detail=message)
    return logs


def user_node(state: GraphState) -> GraphState:
    """Normaliza a entrada do usuário e reinicia os logs de debug do turno.

    Os logs são por-turno (não acumulam entre perguntas) — quem acumula entre turnos é
    `history`, no MemoryNode. Sem esse reset, como o checkpointer do LangGraph persiste o
    state pelo thread_id, `logs` cresceria carregando os logs de todos os turnos anteriores
    a cada novo turno, e a UI (que também acumula) duplicaria essas entradas a cada pergunta.
    """
    question = state["question"].strip()
    return {
        "question": question,
        "logs": _append_log([], "UserNode", f"Pergunta recebida: {question}"),
    }


def planner_node(state: GraphState) -> GraphState:
    """Decide, via LLM, qual agente especializado deve tratar a pergunta (considerando o
    histórico recente da conversa, para perguntas de acompanhamento)."""
    route = decide_route(state["question"], history=state.get("history", []))
    return {
        "route": route,
        "logs": _append_log(state["logs"], "PlannerNode", f"Rota escolhida: {route}"),
    }


def executor_node(state: GraphState) -> GraphState:
    """Despacha a execução para o agente especializado escolhido pelo PlannerNode."""
    route = state["route"]
    question = state["question"]
    history = state.get("history", [])

    has_context = True
    if route == ROUTE_RAG:
        answer, rag_result = run_rag_agent(question, history=history)
        has_context = rag_result.has_context
    elif route == "sql":
        answer = run_sql_agent(question, history=history)
    elif route == "weather":
        answer = run_weather_agent(question, history=history)
    else:
        answer = run_web_search_agent(question, history=history)

    return {
        "answer": answer,
        "has_context": has_context,
        "logs": _append_log(state["logs"], "ExecutorNode", f"Executado agente '{route}'"),
    }


def fallback_web_search_node(state: GraphState) -> GraphState:
    """Fallback: quando o RAG não encontra contexto, cai para busca na web."""
    answer = run_web_search_agent(state["question"], history=state.get("history", []))
    return {
        "answer": answer,
        "logs": _append_log(state["logs"], "FallbackWebSearch", "RAG sem contexto, usando busca web"),
    }


def memory_node(state: GraphState) -> GraphState:
    """Persiste o turno atual no histórico da conversa (isso sim acumula entre turnos —
    é a memória de fato usada pelos outros nós, diferente de `logs`)."""
    history = list(state.get("history", []))
    history.append({"question": state["question"], "answer": state["answer"]})
    return {
        "history": history,
        "logs": _append_log(state["logs"], "MemoryNode", "Turno salvo no histórico"),
    }


def route_after_executor(state: GraphState) -> str:
    """Edge condicional: se o RAG não teve contexto, cai para o fallback de busca web."""
    if state["route"] == ROUTE_RAG and not state.get("has_context", True):
        return "fallback_web_search"
    return "memory"
