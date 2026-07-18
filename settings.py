from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_supports_temperature: bool = True

    tavily_api_key: str = ""

    # Vetor DB: "chroma" (default, via docker-compose) ou "azure_search" (bônus Foundry)
    vector_backend: str = "chroma"
    chroma_host: str = "chroma"
    chroma_port: int = 8000
    chroma_collection: str = "faq_docs"
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index_name: str = "faq-docs"

    # SQL: "postgres" (default, via docker-compose) ou "mssql" (bônus Foundry / Azure SQL)
    sql_dialect: str = "postgres"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "assistant"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/assistant"

    weather_rate_limit_per_minute: int = 10
    web_search_rate_limit_per_minute: int = 10

    log_level: str = "INFO"

    # Azure AI Foundry Agent Service (bônus, opcional — ver foundry/README.md)
    azure_ai_foundry_project_endpoint: str = ""
    azure_ai_foundry_agent_name: str = "mini-assistant-multi-agent"


settings = Settings()
