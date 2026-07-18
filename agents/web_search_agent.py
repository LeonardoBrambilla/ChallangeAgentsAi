from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from history_utils import format_history
from llm_factory import get_chat_llm
from tools.web_search_tool import WebSearchInput, web_search

_SYSTEM_PROMPT = (
    "Você é um assistente que consolida resultados de busca na web em uma resposta "
    "clara e objetiva, sempre citando as fontes usadas (URLs) ao final. Use o histórico "
    "recente da conversa (se houver) para entender perguntas de acompanhamento."
)


def run_web_search_agent(question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Busca na web via Tavily e usa o LLM para consolidar a resposta com links-fonte."""
    result = web_search(WebSearchInput(query=question))

    llm = get_chat_llm()
    history_block = format_history(history or [])
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"{history_block}\n\n"
                f"Pergunta do usuário: {question}\n\n"
                f"Resultados da busca:\n{result.answer}\n\n"
                f"Fontes disponíveis: {result.sources}\n\n"
                "Responda à pergunta e liste as fontes usadas."
            )
        ),
    ]
    response = llm.invoke(messages)
    return response.content
