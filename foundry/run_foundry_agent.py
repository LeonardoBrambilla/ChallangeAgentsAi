"""Roda uma pergunta contra o Agent já provisionado no Azure AI Foundry (via
`provision_agent.py`), tratando o ciclo de tool calls — este módulo é o substituto do
LangGraph quando se opera no modo Foundry (bônus do desafio): aqui é o próprio Agent
Service do Azure quem decide a rota entre as tools, não o `PlannerNode` do LangGraph.

Uso:
    python -m foundry.run_foundry_agent "Qual o prazo de reembolso de um pedido?"
"""
import sys
import time
from typing import Optional

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from foundry.agent_functions import execute_tool_call
from foundry.provision_agent import provision_agent
from settings import settings


def ask(question: str, credential: Optional[TokenCredential] = None) -> str:
    credential = credential or DefaultAzureCredential()
    client = AgentsClient(
        endpoint=settings.azure_ai_foundry_project_endpoint,
        credential=credential,
    )

    agent_id = provision_agent(credential=credential)
    thread = client.threads.create()
    client.messages.create(thread_id=thread.id, role="user", content=question)
    run = client.runs.create(thread_id=thread.id, agent_id=agent_id)

    while run.status in ("queued", "in_progress", "requires_action"):
        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for call in tool_calls:
                if isinstance(call, RequiredFunctionToolCall):
                    output = execute_tool_call(call.function.name, call.function.arguments)
                    tool_outputs.append(ToolOutput(tool_call_id=call.id, output=output))
            client.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)

        time.sleep(1)
        run = client.runs.get(thread_id=thread.id, run_id=run.id)

    if run.status == "failed":
        raise RuntimeError(f"Run falhou: {run.last_error}")

    last_message = client.messages.get_last_message_text_by_role(thread_id=thread.id, role=MessageRole.AGENT)
    return last_message.text.value if last_message else ""


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Qual o prazo de reembolso de um pedido?"
    print(ask(question))
