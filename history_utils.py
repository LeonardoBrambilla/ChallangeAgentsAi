from typing import Any, Dict, List

MAX_HISTORY_TURNS = 3


def format_history(history: List[Dict[str, Any]], max_turns: int = MAX_HISTORY_TURNS) -> str:
    """Formata os últimos turnos da conversa como texto simples para dar contexto ao LLM.

    Retorna string vazia se não há histórico, para os prompts poderem omitir a seção
    inteira sem checagem condicional espalhada em cada agente.
    """
    if not history:
        return ""

    recent = history[-max_turns:]
    lines = [f"Usuário: {turn['question']}\nAssistente: {turn['answer']}" for turn in recent]
    return "Histórico recente da conversa:\n" + "\n\n".join(lines)
