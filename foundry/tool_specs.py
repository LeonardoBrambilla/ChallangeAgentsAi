"""Especificação das 4 tools como function tools do Azure AI Foundry Agent Service.

Reaproveita os mesmos schemas Pydantic de `tools/*.py` (entrada tipada) em vez de duplicar
a definição do contrato — a mesma tool serve tanto o grafo LangGraph (modo default) quanto
um Agent do Foundry (bônus, quando `AZURE_AI_FOUNDRY_PROJECT_ENDPOINT` está configurado).
"""
from azure.ai.agents.models import FunctionDefinition, FunctionToolDefinition

from tools.sql_tool import SqlQueryInput
from tools.vector_search_tool import VectorSearchInput
from tools.weather_tool import WeatherInput
from tools.web_search_tool import WebSearchInput

TOOL_DESCRIPTIONS = {
    "web_search": "Busca informações atuais na web (Tavily) e retorna um resumo com links-fonte.",
    "vector_search": "Faz busca por similaridade na base vetorial de FAQs/políticas da empresa.",
    "sql_query": "Executa uma query SQL somente-leitura (SELECT) sobre as tabelas clientes/pedidos.",
    "get_weather": "Consulta a previsão do tempo atual de uma cidade.",
}

_SCHEMAS = {
    "web_search": WebSearchInput,
    "vector_search": VectorSearchInput,
    "sql_query": SqlQueryInput,
    "get_weather": WeatherInput,
}


def build_function_tool_definitions() -> list[FunctionToolDefinition]:
    """Gera as definições de function tools no formato do SDK `azure-ai-agents`
    (`FunctionToolDefinition`/`FunctionDefinition`)."""
    definitions = []
    for name, schema_cls in _SCHEMAS.items():
        schema = schema_cls.model_json_schema()
        definitions.append(
            FunctionToolDefinition(
                function=FunctionDefinition(
                    name=name,
                    description=TOOL_DESCRIPTIONS[name],
                    parameters={
                        "type": "object",
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", []),
                    },
                )
            )
        )
    return definitions
