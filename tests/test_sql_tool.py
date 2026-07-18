import pytest

from tools.sql_tool import SqlQueryInput, UnsafeQueryError, _validate_query, run_sql_query


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM clientes",
        "SELECT nome, cidade FROM clientes WHERE cidade = 'São Paulo'",
        "SELECT p.produto, c.nome FROM pedidos p JOIN clientes c ON p.cliente_id = c.id",
    ],
)
def test_validate_query_allows_safe_selects(query):
    _validate_query(query)  # não deve levantar exceção


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE clientes",
        "DELETE FROM clientes",
        "INSERT INTO clientes (nome) VALUES ('x')",
        "SELECT * FROM usuarios_admin",
        "UPDATE pedidos SET status = 'entregue'",
    ],
)
def test_validate_query_blocks_unsafe_queries(query):
    with pytest.raises(UnsafeQueryError):
        _validate_query(query)


class _FakeResult:
    def keys(self):
        return ["nome", "cidade"]

    def fetchall(self):
        return [("Ana Souza", "São Paulo")]


class _FakeConnection:
    def execute(self, statement):
        return _FakeResult()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeEngine:
    def connect(self):
        return _FakeConnection()


def test_run_sql_query_returns_typed_result():
    result = run_sql_query(SqlQueryInput(query="SELECT nome, cidade FROM clientes"), engine=_FakeEngine())

    assert result.columns == ["nome", "cidade"]
    assert result.row_count == 1
    assert result.rows[0] == ["Ana Souza", "São Paulo"]
