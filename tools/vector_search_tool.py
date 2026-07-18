from typing import Any, List, Optional

from pydantic import BaseModel, Field

from logging_config import configure_logging, log_event
from settings import settings
from vector_db.store_factory import get_vector_store

logger = configure_logging(settings.log_level)

_vector_store: Optional[Any] = None


def _get_vector_store() -> Any:
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store


class VectorSearchInput(BaseModel):
    query: str = Field(..., description="Pergunta do usuário para buscar contexto nos documentos ingeridos")
    top_k: int = Field(default=4, ge=1, le=10)


class VectorSearchResult(BaseModel):
    chunks: List[str]
    sources: List[str]
    has_context: bool


def vector_search(input_data: VectorSearchInput, store: Optional[Any] = None) -> VectorSearchResult:
    """Faz similarity search na base vetorial (Chroma) previamente populada por ingest.py."""
    log_event(logger, "vector_search_tool.call", query=input_data.query)

    vector_store = store or _get_vector_store()
    docs = vector_store.similarity_search(input_data.query, k=input_data.top_k)

    chunks = [doc.page_content for doc in docs]
    sources = [doc.metadata.get("source", "unknown") for doc in docs]

    result = VectorSearchResult(chunks=chunks, sources=sources, has_context=len(chunks) > 0)
    log_event(logger, "vector_search_tool.result", num_chunks=len(chunks))
    return result
