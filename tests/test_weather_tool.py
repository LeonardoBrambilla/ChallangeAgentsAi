import httpx
import pytest

from tools.weather_tool import WeatherInput, get_weather


class _FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class _FakeClient:
    def __init__(self):
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        if "geocoding" in url:
            return _FakeResponse({"results": [{"name": "São Paulo", "latitude": -23.5, "longitude": -46.6}]})
        return _FakeResponse({"current": {"temperature_2m": 25.5, "weather_code": 0}})


def test_get_weather_returns_expected_result():
    client = _FakeClient()
    result = get_weather(WeatherInput(city="São Paulo"), client=client)

    assert result.city == "São Paulo"
    assert result.temperature_c == 25.5
    assert result.description == "céu limpo"
    assert client.calls == 2


class _EmptyGeocodingClient:
    def get(self, url, params=None, timeout=None):
        return _FakeResponse({"results": []})


def test_get_weather_raises_for_unknown_city():
    with pytest.raises(ValueError):
        get_weather(WeatherInput(city="CidadeInexistente"), client=_EmptyGeocodingClient())
