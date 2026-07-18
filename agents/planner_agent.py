from typing import Any, Dict, List, Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from history_utils import format_history
from llm_factory import get_chat_llm

# Rotas como constantes (em vez de strings soltas) para evitar drift entre este módulo e
# as comparações em graph/nodes.py — um typo em qualquer um dos dois lugares vira erro de
# tipo/atributo em vez de silenciosamente cair no branch errado.
ROUTE_RAG = "rag"
ROUTE_SQL = "sql"
ROUTE_WEATHER = "weather"
ROUTE_WEB_SEARCH = "web_search"

Route = Literal["rag", "sql", "weather", "web_search"]

_SYSTEM_PROMPT = """
Você é o roteador de um assistente multi-agente. Dada a pergunta do usuário (e, se houver,
o histórico recente da conversa), escolha QUAL agente especializado deve respondê-la:

- "rag": perguntas sobre políticas, FAQs ou documentação interna da empresa.
- "sql": perguntas sobre dados estruturados de clientes ou pedidos (contagens, totais, filtros).
- "weather": perguntas sobre previsão do tempo/clima de alguma cidade.
- "web_search": qualquer outra pergunta geral, que exija busca na web ou informação atual.

Use o histórico para resolver perguntas de acompanhamento (ex. "e em outra cidade?" após uma
pergunta de clima deve continuar roteando para "weather").

Responda somente com uma dessas rotas.
"""


class RouteDecision(BaseModel):
    route: Route = Field(..., description="Rota escolhida para responder a pergunta")


def decide_route(question: str, history: Optional[List[Dict[str, Any]]] = None) -> Route:
    """Usa o LLM para decidir, a partir do prompt do usuário e do histórico recente, qual
    agente/tool acionar."""
    llm = get_chat_llm()
    structured_llm = llm.with_structured_output(RouteDecision)

    history_block = format_history(history or [])
    content = f"{history_block}\n\nPergunta atual: {question}" if history_block else question

    decision: RouteDecision = structured_llm.invoke(
        [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=content)]
    )
    return decision.route
