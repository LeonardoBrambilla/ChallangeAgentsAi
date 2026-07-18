"""Provisiona (cria/atualiza) o agente multi-tool como um workflow do Azure AI Foundry
Agent Service — a alternativa ao LangGraph quando se adota Foundry (bônus do desafio).

Requer um projeto Azure AI Foundry já criado (endpoint em
`AZURE_AI_FOUNDRY_PROJECT_ENDPOINT`) e as libs extras em `foundry/requirements-foundry.txt`
(não fazem parte da imagem Docker default, para não pesar o caminho principal do desafio).

Uso:
    pip install -r foundry/requirements-foundry.txt
    python -m foundry.provision_agent
"""
from typing import Optional

from azure.ai.agents import AgentsClient
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from foundry.tool_specs import build_function_tool_definitions
from settings import settings

INSTRUCTIONS = """
Você é um assistente multi-agente. Para cada pergunta, decida sozinho qual das ferramentas
disponíveis usar (busca web, busca vetorial em FAQs/políticas, consulta SQL de
clientes/pedidos, ou previsão do tempo) e responda em linguagem natural, citando fontes
quando aplicável. Se a busca vetorial não retornar contexto suficiente, use a busca web
como alternativa.
""".strip()


def provision_agent(credential: Optional[TokenCredential] = None) -> str:
    """Cria (ou atualiza, se já existir com o mesmo nome) o Agent no projeto Foundry e
    retorna o `agent.id` provisionado.

    `credential` é injetável (default `DefaultAzureCredential()`, que via `az login` local
    ou managed identity em produção) — útil para testes com uma credencial já obtida.
    """
    client = AgentsClient(
        endpoint=settings.azure_ai_foundry_project_endpoint,
        credential=credential or DefaultAzureCredential(),
    )

    existing = next(
        (a for a in client.list_agents() if a.name == settings.azure_ai_foundry_agent_name),
        None,
    )

    tools = build_function_tool_definitions()

    if existing:
        agent = client.update_agent(
            existing.id,
            model=settings.azure_openai_chat_deployment,
            instructions=INSTRUCTIONS,
            tools=tools,
        )
    else:
        agent = client.create_agent(
            model=settings.azure_openai_chat_deployment,
            name=settings.azure_ai_foundry_agent_name,
            instructions=INSTRUCTIONS,
            tools=tools,
        )

    return agent.id


if __name__ == "__main__":
    agent_id = provision_agent()
    print(f"Agent provisionado no Azure AI Foundry: {agent_id}")
