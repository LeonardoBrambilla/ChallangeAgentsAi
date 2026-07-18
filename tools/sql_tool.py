from typing import Any, List

import sqlglot
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from pydantic import BaseModel, Field

from logging_config import configure_logging, log_event
from settings import settings

logger = configure_logging(settings.log_level)

ALLOWED_TABLES = {"clientes", "pedidos"}
FORBIDDEN_KEYWORDS = {"insert", "update", "delete", "drop", "alter", "create", "truncate", "grant", "attach"}

_engine: Engine | None = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


class SqlQueryInput(BaseModel):
    query: str = Field(..., description="Query SQL somente-leitura (SELECT) a ser executada")


class SqlQueryResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


class UnsafeQueryError(ValueError):
    pass


def _validate_query(query: str) -> None:
    """Bloqueia qualquer coisa que não seja um SELECT sobre tabelas na whitelist.

    O dialeto (`settings.sql_dialect`) é configurável para suportar tanto Postgres
    (default, via docker-compose) quanto Azure SQL/mssql (bônus Azure Foundry) sem
    duplicar a lógica de validação.
    """
    try:
        parsed = sqlglot.parse_one(query, read=settings.sql_dialect)
    except Exception as exc:
        raise UnsafeQueryError(f"Query SQL inválida: {exc}") from exc

    if parsed.key != "select":
        raise UnsafeQueryError("Somente queries SELECT são permitidas.")

    lowered = query.lower()
    if any(keyword in lowered for keyword in FORBIDDEN_KEYWORDS):
        raise UnsafeQueryError("Query contém palavra-chave não permitida.")

    tables = {t.name.lower() for t in parsed.find_all(sqlglot.exp.Table)}
    if not tables.issubset(ALLOWED_TABLES):
        raise UnsafeQueryError(f"Tabelas não permitidas: {tables - ALLOWED_TABLES}")


def run_sql_query(input_data: SqlQueryInput, engine: Engine | None = None) -> SqlQueryResult:
    """Executa uma query SQL parametrizada e validada contra o Postgres, retornando resultado tipado."""
    log_event(logger, "sql_tool.call", query=input_data.query)
    _validate_query(input_data.query)

    db_engine = engine or _get_engine()
    with db_engine.connect() as conn:
        result = conn.execute(text(input_data.query))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]

    log_event(logger, "sql_tool.result", row_count=len(rows))
    return SqlQueryResult(columns=columns, rows=rows, row_count=len(rows))
