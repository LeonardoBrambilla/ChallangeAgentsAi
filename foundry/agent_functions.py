"""Dispatcher das function tools para o loop de execução do Foundry Agent.

Diferente do modo default (LangGraph), aqui é o próprio Agent do Azure AI Foundry quem
decide qual função chamar e formula a resposta final — por isso despachamos direto para as
tools "cruas" (`tools/*.py`), sem passar pelos `agents/*.py` (que fariam uma segunda chamada
de LLM redundante só para reformular texto que o Foundry Agent já vai reformular).
"""
import json
from typing import Any, Callable, Dict

from tools.sql_tool import SqlQueryInput, UnsafeQueryError, run_sql_query
from tools.vector_search_tool import VectorSearchInput, vector_search
from tools.weather_tool import WeatherInput, get_weather
from tools.web_search_tool import WebSearchInput, web_search


def _run_web_search(args: Dict[str, Any]) -> dict:
    result = web_search(WebSearchInput(**args))
    return result.model_dump()


def _run_vector_search(args: Dict[str, Any]) -> dict:
    result = vector_search(VectorSearchInput(**args))
    return result.model_dump()


def _run_sql_query(args: Dict[str, Any]) -> dict:
    try:
        result = run_sql_query(SqlQueryInput(**args))
        return result.model_dump()
    except UnsafeQueryError as exc:
        return {"error": str(exc)}


def _run_get_weather(args: Dict[str, Any]) -> dict:
    result = get_weather(WeatherInput(**args))
    return result.model_dump()


FUNCTION_DISPATCH: Dict[str, Callable[[Dict[str, Any]], dict]] = {
    "web_search": _run_web_search,
    "vector_search": _run_vector_search,
    "sql_query": _run_sql_query,
    "get_weather": _run_get_weather,
}


def execute_tool_call(function_name: str, arguments_json: str) -> str:
    """Executa uma function tool a partir do formato bruto de tool call do Foundry
    (nome + argumentos serializados em JSON) e retorna o resultado também serializado."""
    handler = FUNCTION_DISPATCH.get(function_name)
    if handler is None:
        return json.dumps({"error": f"Função desconhecida: {function_name}"})

    args = json.loads(arguments_json) if arguments_json else {}
    try:
        result = handler(args)
    except Exception as exc:  # noqa: BLE001 — erro de qualquer tool vira resposta de erro pro Agent
        result = {"error": str(exc)}
    return json.dumps(result, ensure_ascii=False)
