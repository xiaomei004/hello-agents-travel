"""根据城市和天气用 Tavily 搜索景点推荐。"""

from __future__ import annotations

import os

from ..config import is_placeholder


def get_attraction(city: str, weather: str) -> str:
    """返回景点推荐文本；失败时返回以“错误:”开头的字符串。"""
    city = city.strip()
    weather = weather.strip()
    if not city:
        return "错误:城市名称不能为空。"

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return (
            "错误:未配置 TAVILY_API_KEY。请复制 .env.example 为 .env，"
            "填入 Tavily API Key 后重试。"
        )
    if is_placeholder(api_key):
        return (
            "错误:TAVILY_API_KEY 还是示例占位符。"
            "请打开 .env，把 tvly-your-tavily-key 换成真实 Key。"
        )

    # 延迟导入：这样只查天气时，即使没装 tavily-python 也不会整个项目启动失败。
    try:
        from tavily import TavilyClient
    except ImportError:
        return "错误:未安装 tavily-python。请运行 pip install -r requirements.txt。"

    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            include_answer=True,
            max_results=5,
        )
    except Exception as exc:  # noqa: BLE001 - 工具边界统一转成 Observation
        return f"错误:执行 Tavily 搜索时出现问题 - {exc}"

    answer = response.get("answer")
    if answer:
        return str(answer)

    results = response.get("results") or []
    if not results:
        return "抱歉，没有找到相关的旅游景点推荐。"

    lines = [
        f"- {item.get('title', '未命名')}: {item.get('content', '')}"
        for item in results[:5]
    ]
    return "根据搜索，为您找到以下信息:\n" + "\n".join(lines)
