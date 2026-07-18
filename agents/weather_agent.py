from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from history_utils import format_history
from llm_factory import get_chat_llm
from tools.weather_tool import WeatherInput, get_weather

_EXTRACT_CITY_PROMPT = (
    "Extraia apenas o nome da cidade mencionada na pergunta do usuário sobre previsão do "
    "tempo. Se a pergunta for uma continuação (ex. 'e em outra cidade?'), use o histórico "
    "da conversa para identificar a cidade certa. Responda apenas com o nome da cidade, "
    "sem mais nada."
)

_ANSWER_PROMPT = (
    "Você responde perguntas sobre previsão do tempo em linguagem natural, de forma "
    "amigável e concisa, a partir dos dados brutos fornecidos."
)


def run_weather_agent(question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Extrai a cidade da pergunta (usando histórico se for uma continuação), consulta o
    Open-Meteo e responde em linguagem natural."""
    llm = get_chat_llm()
    history_block = format_history(history or [])

    city = llm.invoke(
        [
            SystemMessage(content=_EXTRACT_CITY_PROMPT),
            HumanMessage(content=f"{history_block}\n\nPergunta atual: {question}" if history_block else question),
        ]
    ).content.strip()

    try:
        weather = get_weather(WeatherInput(city=city))
    except Exception as exc:
        return f"Não consegui obter a previsão do tempo para '{city}': {exc}"

    answer_messages = [
        SystemMessage(content=_ANSWER_PROMPT),
        HumanMessage(
            content=(
                f"Pergunta: {question}\n"
                f"Cidade: {weather.city}\n"
                f"Temperatura atual: {weather.temperature_c}°C\n"
                f"Condição: {weather.description}"
            )
        ),
    ]
    return llm.invoke(answer_messages).content
