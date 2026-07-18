from functools import lru_cache

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from settings import settings


@lru_cache(maxsize=None)
def get_chat_llm(temperature: float = 0) -> AzureChatOpenAI:
    """Cliente de chat cacheado por combinação de temperatura — evita recriar o cliente
    HTTP/SDK a cada chamada de agente (cada agente chama isso ao menos uma vez por turno)."""
    kwargs = {
        "azure_endpoint": settings.azure_openai_endpoint,
        "api_key": settings.azure_openai_api_key,
        "api_version": settings.azure_openai_api_version,
        "azure_deployment": settings.azure_openai_chat_deployment,
    }
    # Alguns modelos (ex. família o1/gpt-5 "reasoning") só aceitam temperature=1 (o default
    # da API, não o default de 0.7 do langchain) e rejeitam qualquer outro valor.
    kwargs["temperature"] = temperature if settings.azure_openai_supports_temperature else 1
    return AzureChatOpenAI(**kwargs)


@lru_cache(maxsize=None)
def get_embeddings() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_embedding_deployment,
    )
