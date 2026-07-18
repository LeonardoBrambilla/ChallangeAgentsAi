from unittest.mock import MagicMock, patch

from agents.sql_agent import _nl2sql_prompt
from settings import settings


def test_nl2sql_prompt_reflects_postgres_dialect_by_default():
    assert settings.sql_dialect == "postgres"
    assert "PostgreSQL" in _nl2sql_prompt()


def test_nl2sql_prompt_switches_to_mssql_when_configured():
    with patch.object(settings, "sql_dialect", "mssql"):
        prompt = _nl2sql_prompt()

    assert "T-SQL" in prompt
    assert "PostgreSQL" not in prompt


def test_run_sql_agent_passes_history_to_llm():
    from agents.sql_agent import run_sql_agent

    fake_llm = MagicMock()
    fake_llm.invoke.side_effect = [
        MagicMock(content="SELECT nome FROM clientes"),
        MagicMock(content="Resposta final"),
    ]

    with patch("agents.sql_agent.get_chat_llm", return_value=fake_llm), patch(
        "agents.sql_agent.run_sql_query"
    ) as mock_run_query:
        mock_run_query.return_value.columns = ["nome"]
        mock_run_query.return_value.rows = [["Ana"]]

        run_sql_agent("Quem são os clientes?", history=[{"question": "oi", "answer": "olá"}])

    nl2sql_call_messages = fake_llm.invoke.call_args_list[0][0][0]
    human_message = nl2sql_call_messages[-1]
    assert "Histórico recente" in human_message.content
    assert "oi" in human_message.content
