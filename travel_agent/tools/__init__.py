"""工具注册表：把工具名映射到实际函数。"""

from __future__ import annotations

from collections.abc import Callable

from .attractions import get_attraction
from .weather import get_weather

available_tools: dict[str, Callable[..., str]] = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

__all__ = ["available_tools", "get_attraction", "get_weather"]
