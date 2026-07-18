from unittest.mock import patch

import pytest

from tools.web_search_tool import WebSearchInput, _get_tavily_client, web_search


@pytest.fixture(autouse=True)
def _clear_tavily_client_cache():
    # _get_tavily_client é cacheado por max_results (lru_cache) para reusar o client HTTP
    # em produção; nos testes, limpamos entre casos para que cada `patch` valha de fato.
    _get_tavily_client.cache_clear()
    yield
    _get_tavily_client.cache_clear()


def test_web_search_consolidates_answer_and_sources():
    fake_results = [
        {"url": "https://example.com/a", "content": "Conteúdo A"},
        {"url": "https://example.com/b", "content": "Conteúdo B"},
    ]

    with patch("tools.web_search_tool.TavilySearchResults") as mock_tool_cls:
        mock_tool_cls.return_value.invoke.return_value = fake_results

        result = web_search(WebSearchInput(query="o que é langgraph?"))

    assert result.sources == ["https://example.com/a", "https://example.com/b"]
    assert "Conteúdo A" in result.answer
    assert "Conteúdo B" in result.answer


def test_web_search_handles_no_results():
    with patch("tools.web_search_tool.TavilySearchResults") as mock_tool_cls:
        mock_tool_cls.return_value.invoke.return_value = []

        result = web_search(WebSearchInput(query="pergunta sem resultado"))

    assert result.sources == []
    assert result.answer == "Nenhum resultado encontrado."
