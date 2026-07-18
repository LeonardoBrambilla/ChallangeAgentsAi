from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from history_utils import format_history
from llm_factory import get_chat_llm
from tools.vector_search_tool import VectorSearchInput, VectorSearchResult, vector_search

_SYSTEM_PROMPT = (
    "Você responde perguntas usando apenas o contexto fornecido, extraído da base de "
    "documentos/FAQs da empresa. Cite os documentos-fonte usados. Use o histórico recente "
    "da conversa (se houver) para entender perguntas de acompanhamento."
)


def run_rag_agent(
    question: str, history: Optional[List[Dict[str, Any]]] = None
) -> tuple[str, VectorSearchResult]:
    """Faz similarity search na base vetorial e usa o LLM para responder com o contexto encontrado.

    Retorna (resposta, resultado_da_busca) para que o grafo saiba se deve cair no fallback
    de busca web quando has_context=False.
    """
    result = vector_search(VectorSearchInput(query=question))

    if not result.has_context:
        return "Não encontrei contexto suficiente na base de documentos.", result

    llm = get_chat_llm()
    context = "\n\n".join(result.chunks)
    history_block = format_history(history or [])
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"{history_block}\n\n"
                f"Contexto:\n{context}\n\n"
                f"Fontes: {result.sources}\n\n"
                f"Pergunta: {question}"
            )
        ),
    ]
    response = llm.invoke(messages)
    return response.content, result
