import sys
import types

from travel_agent.tools.attractions import get_attraction
from travel_agent.tools.weather import get_weather


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "current_condition": [
                {
                    "weatherDesc": [{"value": "晴"}],
                    "temp_C": "20",
                    "humidity": "50",
                }
            ]
        }


def test_get_weather_empty_city() -> None:
    assert get_weather(" ") == "错误:城市名称不能为空。"


def test_get_weather_parses_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "travel_agent.tools.weather.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    result = get_weather("武汉")

    assert "晴" in result
    assert "20" in result


def test_get_attraction_without_key(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    assert "未配置" in get_attraction("武汉", "晴")


def test_get_attraction_rejects_placeholder(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-your-tavily-key")

    assert "占位符" in get_attraction("武汉", "晴")


def test_get_attraction_uses_tavily(monkeypatch) -> None:
    class FakeTavilyClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "tvly-real"

        def search(self, **kwargs) -> dict:
            return {"answer": "推荐东湖"}

    monkeypatch.setenv("TAVILY_API_KEY", "tvly-real")
    monkeypatch.setitem(
        sys.modules,
        "tavily",
        types.SimpleNamespace(TavilyClient=FakeTavilyClient),
    )

    assert get_attraction("武汉", "晴") == "推荐东湖"
