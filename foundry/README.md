# Modo Azure AI Foundry (bônus, opcional)

Este diretório implementa a alternativa ao LangGraph mencionada no desafio: **provisionar
os agentes como workflows do Azure AI Foundry Agent Service**, em vez de orquestrar via
`graph/build_graph.py`. Não faz parte do caminho default de `docker compose up` — o Chroma
+ Postgres + LangGraph continuam sendo a stack principal, testada e validada de ponta a
ponta neste projeto.

## O que foi implementado

- `tool_specs.py` — converte os mesmos schemas Pydantic das tools (`tools/*.py`) em
  definições de *function tools* no formato do Foundry/Azure OpenAI function-calling. Zero
  duplicação de contrato: a mesma tool serve o LangGraph e o Foundry.
- `agent_functions.py` — dispatcher que executa a tool correta a partir do nome da função e
  dos argumentos que o Agent do Foundry decidir enviar.
- `provision_agent.py` — cria (ou atualiza) o Agent no seu projeto Foundry, com as 4
  function tools registradas.
- `run_foundry_agent.py` — roda uma pergunta contra esse Agent, tratando o ciclo de
  `requires_action` → executa a tool → `submit_tool_outputs`, até a resposta final.

## Como usar

Requer um **projeto Azure AI Foundry já criado** (não provisiono isso por você — exige
acesso à sua assinatura Azure):

```bash
pip install -r foundry/requirements-foundry.txt

# no .env do projeto:
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=https://<recurso>.services.ai.azure.com/api/projects/<projeto>
AZURE_AI_FOUNDRY_AGENT_NAME=mini-assistant-multi-agent   # opcional, já é o default

az login   # DefaultAzureCredential usa sua sessão do Azure CLI

python -m foundry.provision_agent
python -m foundry.run_foundry_agent "Qual o prazo de reembolso de um pedido?"
```

> O endpoint do projeto (`AZURE_AI_FOUNDRY_PROJECT_ENDPOINT`) precisa ser o do **projeto**
> dentro do recurso Cognitive Services/AI Foundry (`.../api/projects/<nome-do-projeto>`),
> não o nome de exibição que você deu no portal — se dúvida, confirme com:
> `az rest --method get --url "https://management.azure.com/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<recurso>/projects?api-version=2025-06-01"`
> e use o valor em `properties.endpoints["AI Foundry API"]`.

## ✅ Testado ao vivo

Diferente da primeira versão desta entrega, este módulo **foi validado de ponta a ponta
contra um projeto Azure AI Foundry real** (`az login` + `AgentsClient`), com dois cenários:

1. Pergunta de RAG ("Qual o prazo de reembolso de um pedido?") → o Agent do Foundry decidiu
   sozinho chamar a function tool `vector_search`, recebeu o contexto do Chroma via
   `agent_functions.execute_tool_call`, e formulou uma resposta correta citando a política.
2. Pergunta de clima ("Qual a previsão do tempo em São Paulo agora?") → o Agent chamou
   `get_weather` e respondeu com a temperatura/condição reais do Open-Meteo.

Isso confirma que o roteamento multi-tool, o dispatcher (`agent_functions.py`) e o ciclo
`requires_action` → `submit_tool_outputs` → resposta final estão corretos.

### Correções feitas durante o teste ao vivo (SDK mudou bastante entre previews)

O SDK real instalável (`azure-ai-projects==2.3.0` + `azure-ai-agents==1.1.0`) mudou a API
drasticamente em relação à versão preview (`1.0.0bN`) contra a qual o código foi escrito
originalmente sem acesso a um projeto real para validar:

- **Não existe mais `AIProjectClient().agents`** — os agentes são gerenciados por um cliente
  dedicado, `azure.ai.agents.AgentsClient`, instanciado direto com o mesmo `endpoint`.
- **`.threads`, `.messages`, `.runs`** são sub-clientes de instância do `AgentsClient`
  (`client.threads.create()`, `client.messages.create(...)`,
  `client.runs.create(...)`/`.get(...)`/`.submit_tool_outputs(...)`), não métodos
  `create_thread`/`create_message`/`create_run` "achatados" como em versões antigas.
- As classes de tool ficam em `azure.ai.agents.models` (não `azure.ai.projects.models`):
  `FunctionToolDefinition`, `FunctionDefinition`, `RequiredFunctionToolCall`,
  `SubmitToolOutputsAction`, `ToolOutput`, `MessageRole`.
- `client.messages.get_last_message_text_by_role(thread_id=..., role=MessageRole.AGENT)`
  substitui o antigo `get_last_text_message_by_role`.
- `azure-ai-projects` propriamente dito **não é mais necessário** no código — só
  `azure-ai-agents` + `azure-identity` (removido de `requirements-foundry.txt`).
- `provision_agent()`/`ask()` agora aceitam um parâmetro `credential` opcional (default
  `DefaultAzureCredential()`), o que permitiu injetar uma credencial de teste sem tocar no
  caminho de produção (que continua usando `az login`/managed identity normalmente).

Isso é uma boa demonstração de por que "código completo mas não testado" é uma categoria de
risco real para SDKs em rápida evolução — sem rodar contra o serviço de verdade, os nomes de
classe/método usados originalmente (baseados na documentação pública na época) já estariam
quebrados na primeira execução.

## Vetor DB e SQL também alternáveis para a stack Foundry

Além dos agentes, o desafio também sugere Azure AI Search como vetorDB e Azure SQL como
banco relacional. Isso **não fica neste diretório** — foi implementado direto nos módulos
principais, sempre com Chroma/Postgres como default:

- `settings.VECTOR_BACKEND=azure_search` (+ `AZURE_SEARCH_ENDPOINT`/`AZURE_SEARCH_API_KEY`/
  `AZURE_SEARCH_INDEX_NAME`) troca o backend usado por `vector_db/store_factory.py`,
  usado tanto por `ingest.py` quanto por `tools/vector_search_tool.py`.
- `settings.SQL_DIALECT=mssql` + apontar `DATABASE_URL` para o seu Azure SQL (driver
  `mssql+pyodbc` ou `mssql+pymssql`, não incluído no `requirements.txt` default para não
  exigir drivers ODBC nativos na imagem Docker principal) troca o dialeto usado pela
  validação `sqlglot` em `tools/sql_tool.py`. Rode `init_mssql.sql` manualmente contra o seu
  Azure SQL antes (schema equivalente ao `init.sql` do Postgres, em T-SQL).
