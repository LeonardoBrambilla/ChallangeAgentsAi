import httpx
from pydantic import BaseModel, Field

from logging_config import configure_logging, log_event
from rate_limiter import RateLimiter
from settings import settings

logger = configure_logging(settings.log_level)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_WEATHER_CODE_DESCRIPTIONS = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "neblina",
    48: "neblina com geada",
    51: "garoa leve",
    61: "chuva leve",
    63: "chuva moderada",
    65: "chuva forte",
    71: "neve leve",
    80: "pancadas de chuva",
    95: "tempestade",
}


_rate_limiter = RateLimiter(settings.weather_rate_limit_per_minute, name="weather")


class WeatherInput(BaseModel):
    city: str = Field(..., description="Nome da cidade para consultar a previsão do tempo")


class WeatherResult(BaseModel):
    city: str
    temperature_c: float
    description: str


def get_weather(input_data: WeatherInput, client: httpx.Client | None = None) -> WeatherResult:
    """Consulta geocoding + forecast do Open-Meteo e retorna a previsão em linguagem natural."""
    log_event(logger, "weather_tool.call", city=input_data.city)
    _rate_limiter.check()

    http_client = client or httpx
    geo_response = http_client.get(
        GEOCODING_URL, params={"name": input_data.city, "count": 1, "language": "pt"}, timeout=10
    )
    geo_response.raise_for_status()
    geo_data = geo_response.json()
    results = geo_data.get("results")
    if not results:
        raise ValueError(f"Cidade não encontrada: {input_data.city}")

    location = results[0]
    latitude, longitude = location["latitude"], location["longitude"]
    resolved_name = location.get("name", input_data.city)

    forecast_response = http_client.get(
        FORECAST_URL,
        params={"latitude": latitude, "longitude": longitude, "current": "temperature_2m,weather_code"},
        timeout=10,
    )
    forecast_response.raise_for_status()
    current = forecast_response.json()["current"]

    weather_code = current.get("weather_code", -1)
    description = _WEATHER_CODE_DESCRIPTIONS.get(weather_code, "condição desconhecida")

    result = WeatherResult(
        city=resolved_name,
        temperature_c=current["temperature_2m"],
        description=description,
    )
    log_event(logger, "weather_tool.result", city=result.city, temperature_c=result.temperature_c)
    return result
