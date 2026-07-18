"""Factory do vector store: Chroma (default, via docker-compose) ou Azure AI Search
(bônus Azure Foundry — usa o mesmo índice tanto na ingestão quanto na busca)."""
from typing import Union

import chromadb
from langchain_chroma import Chroma

from llm_factory import get_embeddings
from settings import settings

VectorStore = Union[Chroma, "AzureSearch"]  # noqa: F821 (forward ref só para type hints)


def get_vector_store() -> VectorStore:
    embeddings = get_embeddings()

    if settings.vector_backend == "azure_search":
        from langchain_community.vectorstores.azuresearch import AzureSearch

        return AzureSearch(
            azure_search_endpoint=settings.azure_search_endpoint,
            azure_search_key=settings.azure_search_api_key,
            index_name=settings.azure_search_index_name,
            embedding_function=embeddings.embed_query,
        )

    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return Chroma(
        client=client,
        collection_name=settings.chroma_collection,
        embedding_function=embeddings,
    )
