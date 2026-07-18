from functools import lru_cache
from typing import List

from langchain_community.tools.tavily_search import TavilySearchResults
from pydantic import BaseModel, Field

from logging_config import configure_logging, log_event
from rate_limiter import RateLimiter
from settings import settings

logger = configure_logging(settings.log_level)

_rate_limiter = RateLimiter(settings.web_search_rate_limit_per_minute, name="web_search")


@lru_cache(maxsize=None)
def _get_tavily_client(max_results: int) -> TavilySearchResults:
    """Cliente cacheado por `max_results` — evita recriar o client HTTP a cada busca."""
    return TavilySearchResults(max_results=max_results, api_key=settings.tavily_api_key)


class WebSearchInput(BaseModel):
    query: str = Field(..., description="Pergunta do usuário a ser pesquisada na web")
    max_results: int = Field(default=5, ge=1, le=10)


class WebSearchResult(BaseModel):
    answer: str
    sources: List[str]


def web_search(input_data: WebSearchInput) -> WebSearchResult:
    """Executa busca na web via Tavily e consolida os resultados com links-fonte."""
    log_event(logger, "web_search_tool.call", query=input_data.query)
    _rate_limiter.check()

    search = _get_tavily_client(input_data.max_results)
    raw_results = search.invoke({"query": input_data.query})

    sources: List[str] = []
    snippets: List[str] = []
    for item in raw_results:
        url = item.get("url")
        content = item.get("content", "")
        if url:
            sources.append(url)
        if content:
            snippets.append(content)

    answer = "\n\n".join(snippets) if snippets else "Nenhum resultado encontrado."
    log_event(logger, "web_search_tool.result", num_sources=len(sources))
    return WebSearchResult(answer=answer, sources=sources)
