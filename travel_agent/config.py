"""环境变量与运行配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_QUESTION = (
    "你好，请帮我查询一下明天武汉的天气，"
    "然后根据天气推荐一个合适的旅游景点。"
)
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
PLACEHOLDER_PREFIXES = ("sk-your", "tvly-your")


class ConfigError(RuntimeError):
    """配置缺失，或值仍然是示例占位符。"""


def is_placeholder(value: str | None) -> bool:
    """判断一个 Key 是否仍是 .env.example 里的示例值。"""
    return bool(value) and value.startswith(PLACEHOLDER_PREFIXES)


@dataclass(frozen=True)
class Settings:
    """运行所需配置，集中从环境变量读取。"""

    deepseek_api_key: str
    deepseek_base_url: str = DEFAULT_BASE_URL
    deepseek_model: str = DEFAULT_MODEL
    max_steps: int = 5
    user_prompt: str = DEFAULT_QUESTION
    llm_timeout: float = 60.0

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()

        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise ConfigError(
                "缺少 DEEPSEEK_API_KEY。请复制 .env.example 为 .env，填入 Key 后重试。"
            )
        if is_placeholder(api_key):
            raise ConfigError(
                "DEEPSEEK_API_KEY 还是示例占位符。"
                "请打开 .env，把 sk-your-deepseek-key 换成真实 Key。"
            )

        try:
            max_steps = int(os.getenv("AGENT_MAX_STEPS", "5"))
        except ValueError as exc:
            raise ConfigError("AGENT_MAX_STEPS 必须是整数。") from exc
        if max_steps < 1:
            raise ConfigError("AGENT_MAX_STEPS 必须大于 0。")

        try:
            llm_timeout = float(os.getenv("LLM_TIMEOUT", "60"))
        except ValueError as exc:
            raise ConfigError("LLM_TIMEOUT 必须是数字。") from exc
        if llm_timeout <= 0:
            raise ConfigError("LLM_TIMEOUT 必须大于 0。")

        return cls(
            deepseek_api_key=api_key,
            deepseek_base_url=(
                os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip()
                or DEFAULT_BASE_URL
            ),
            deepseek_model=(
                os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
            ),
            max_steps=max_steps,
            user_prompt=(
                os.getenv("USER_PROMPT", DEFAULT_QUESTION).strip() or DEFAULT_QUESTION
            ),
            llm_timeout=llm_timeout,
        )
