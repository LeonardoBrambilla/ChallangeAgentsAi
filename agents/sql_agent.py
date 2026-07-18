from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from history_utils import format_history
from llm_factory import get_chat_llm
from settings import settings
from tools.sql_tool import SqlQueryInput, UnsafeQueryError, run_sql_query

_SCHEMA_DESCRIPTION = """
Tabelas disponíveis (somente leitura, apenas SELECT):

clientes(id INTEGER, nome TEXT, cidade TEXT, criado_em DATE)
pedidos(id INTEGER, cliente_id INTEGER REFERENCES clientes(id), produto TEXT, valor NUMERIC, status TEXT, criado_em DATE)
"""

# Nome do dialeto em linguagem natural para o prompt, alinhado com `settings.sql_dialect`
# (usado pela validação em tools/sql_tool.py) — sem isso, o LLM sempre geraria SQL em
# sintaxe Postgres mesmo quando configurado para o bônus Azure SQL/mssql.
_DIALECT_NAMES = {
    "postgres": "PostgreSQL",
    "mssql": "T-SQL (SQL Server / Azure SQL)",
}


def _nl2sql_prompt() -> str:
    dialect_name = _DIALECT_NAMES.get(settings.sql_dialect, settings.sql_dialect)
    return (
        "Você traduz perguntas em linguagem natural para uma única query SQL SELECT válida "
        f"no dialeto {dialect_name}, usando apenas as tabelas descritas abaixo. "
        "Use o histórico da conversa (se houver) para resolver perguntas de acompanhamento. "
        "Responda APENAS com a query SQL, sem explicações, sem markdown.\n\n" + _SCHEMA_DESCRIPTION
    )


_ANSWER_PROMPT = (
    "Você recebe o resultado de uma query SQL e deve responder à pergunta original do "
    "usuário em linguagem natural, de forma clara e formatada."
)


def run_sql_agent(question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Gera uma query SQL segura via LLM, executa via sql_tool e formata a resposta em linguagem natural."""
    llm = get_chat_llm()
    history_block = format_history(history or [])

    nl2sql_messages = [
        SystemMessage(content=_nl2sql_prompt()),
        HumanMessage(content=f"{history_block}\n\nPergunta atual: {question}" if history_block else question),
    ]
    sql_query = llm.invoke(nl2sql_messages).content.strip().strip(";").strip("`")

    try:
        result = run_sql_query(SqlQueryInput(query=sql_query))
    except UnsafeQueryError as exc:
        return f"Não foi possível executar essa consulta com segurança: {exc}"

    answer_messages = [
        SystemMessage(content=_ANSWER_PROMPT),
        HumanMessage(
            content=(
                f"Pergunta: {question}\n"
                f"Query executada: {sql_query}\n"
                f"Colunas: {result.columns}\n"
                f"Linhas: {result.rows}"
            )
        ),
    ]
    return llm.invoke(answer_messages).content
