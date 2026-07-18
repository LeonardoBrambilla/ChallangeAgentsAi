from unittest.mock import patch

from graph.build_graph import build_graph
from tools.vector_search_tool import VectorSearchResult


def test_e2e_weather_question_flows_through_graph():
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-weather"}}

    with patch("graph.nodes.decide_route", return_value="weather"), patch(
        "graph.nodes.run_weather_agent", return_value="Em São Paulo está 25°C e céu limpo."
    ):
        final_state = graph.invoke({"question": "Qual a previsão do tempo em São Paulo?"}, config=config)

    assert final_state["route"] == "weather"
    assert "25°C" in final_state["answer"]
    node_names = [entry["node"] for entry in final_state["logs"]]
    assert node_names == ["UserNode", "PlannerNode", "ExecutorNode", "MemoryNode"]


def test_e2e_rag_without_context_falls_back_to_web_search():
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-rag-fallback"}}

    empty_result = VectorSearchResult(chunks=[], sources=[], has_context=False)

    with patch("graph.nodes.decide_route", return_value="rag"), patch(
        "graph.nodes.run_rag_agent",
        return_value=("Não encontrei contexto suficiente na base de documentos.", empty_result),
    ), patch(
        "graph.nodes.run_web_search_agent",
        return_value="Segundo fontes na web, a resposta é X. Fonte: https://example.com",
    ):
        final_state = graph.invoke({"question": "Pergunta totalmente fora do domínio da empresa"}, config=config)

    assert final_state["route"] == "rag"
    assert "Fonte: https://example.com" in final_state["answer"]
    node_names = [entry["node"] for entry in final_state["logs"]]
    assert node_names == ["UserNode", "PlannerNode", "ExecutorNode", "FallbackWebSearch", "MemoryNode"]


def test_e2e_multi_turn_does_not_duplicate_logs_and_accumulates_history():
    """Regressão: `logs` não deve carregar entre turnos (senão duplica na UI), mas
    `history` deve acumular de verdade e ser repassado para o PlannerNode/agente."""
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-multi-turn"}}

    with patch("graph.nodes.decide_route", return_value="weather") as mock_decide_route, patch(
        "graph.nodes.run_weather_agent", return_value="Primeira resposta."
    ):
        first_state = graph.invoke({"question": "Qual o clima em São Paulo?"}, config=config)

    assert [entry["node"] for entry in first_state["logs"]] == [
        "UserNode",
        "PlannerNode",
        "ExecutorNode",
        "MemoryNode",
    ]
    assert first_state["history"] == [{"question": "Qual o clima em São Paulo?", "answer": "Primeira resposta."}]

    with patch("graph.nodes.decide_route", return_value="weather") as mock_decide_route, patch(
        "graph.nodes.run_weather_agent", return_value="Segunda resposta."
    ) as mock_run_weather_agent:
        second_state = graph.invoke({"question": "E no Rio?"}, config=config)

    # logs do 2º turno não devem incluir os nós do 1º turno de novo (fix da duplicação)
    assert [entry["node"] for entry in second_state["logs"]] == [
        "UserNode",
        "PlannerNode",
        "ExecutorNode",
        "MemoryNode",
    ]

    # history, por outro lado, acumula de verdade entre turnos
    assert len(second_state["history"]) == 2
    assert second_state["history"][0]["question"] == "Qual o clima em São Paulo?"
    assert second_state["history"][1] == {"question": "E no Rio?", "answer": "Segunda resposta."}

    # o histórico do 1º turno foi de fato repassado para o roteador e o agente no 2º turno
    _, decide_route_kwargs = mock_decide_route.call_args
    assert decide_route_kwargs["history"][0]["question"] == "Qual o clima em São Paulo?"

    _, run_weather_agent_kwargs = mock_run_weather_agent.call_args
    assert run_weather_agent_kwargs["history"][0]["question"] == "Qual o clima em São Paulo?"
