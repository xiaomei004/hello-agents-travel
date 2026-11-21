"""查询城市实时天气（数据源：wttr.in）。"""

from __future__ import annotations

from urllib.parse import quote

import requests

WTTR_URL = "https://wttr.in/{city}?format=j1&lang=zh"
REQUEST_TIMEOUT = 10


def get_weather(city: str) -> str:
    """返回格式化的天气描述；失败时返回以“错误:”开头的字符串。"""
    city = city.strip()
    if not city:
        return "错误:城市名称不能为空。"

    url = WTTR_URL.format(city=quote(city, safe=""))

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "travel-agent/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        current = data["current_condition"][0]
        description = current["weatherDesc"][0]["value"]
        temperature = current["temp_C"]
        humidity = current.get("humidity")

        result = f"{city}当前天气:{description}，气温{temperature}摄氏度"
        if humidity:
            result += f"，湿度{humidity}%"
        return result

    except requests.exceptions.Timeout:
        return "错误:查询天气超时，请稍后重试。"
    except requests.exceptions.RequestException as exc:
        return f"错误:查询天气时遇到网络问题 - {exc}"
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {exc}"
