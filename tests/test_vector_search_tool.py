from langchain_core.documents import Document

from tools.vector_search_tool import VectorSearchInput, vector_search


class _FakeStore:
    def __init__(self, docs):
        self._docs = docs

    def similarity_search(self, query, k):
        return self._docs[:k]


def test_vector_search_returns_context_when_docs_found():
    docs = [
        Document(page_content="Política de reembolso...", metadata={"source": "politica_reembolso.md"}),
        Document(page_content="Prazo de entrega...", metadata={"source": "politica_entrega.md"}),
    ]
    store = _FakeStore(docs)

    result = vector_search(VectorSearchInput(query="qual o prazo de reembolso?", top_k=2), store=store)

    assert result.has_context is True
    assert result.chunks == ["Política de reembolso...", "Prazo de entrega..."]
    assert result.sources == ["politica_reembolso.md", "politica_entrega.md"]


def test_vector_search_reports_no_context_when_empty():
    store = _FakeStore([])

    result = vector_search(VectorSearchInput(query="pergunta sem contexto"), store=store)

    assert result.has_context is False
    assert result.chunks == []
