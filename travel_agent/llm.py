"""OpenAI 兼容接口的极简客户端。"""

from __future__ import annotations

from openai import OpenAI

from .config import is_placeholder


class LLMError(RuntimeError):
    """调用大模型失败时抛出，避免把错误当成正常回复继续解析。"""


class OpenAICompatibleClient:
    def __init__(
        self,
        model: str,
        api_key: str | None,
        base_url: str,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise LLMError(
                "缺少 DEEPSEEK_API_KEY。请复制 .env.example 为 .env，填入 Key 后重试。"
            )
        if is_placeholder(api_key):
            raise LLMError(
                "DEEPSEEK_API_KEY 还是示例占位符。"
                "请打开 .env，把 sk-your-deepseek-key 换成真实 Key。"
            )
        if not model:
            raise LLMError("缺少模型名称，请设置 DEEPSEEK_MODEL。")

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用大模型并返回纯文本；失败时抛出 LLMError。"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                temperature=0.2,
            )
        except Exception as exc:  # 网络、鉴权、限流、模型名错误都会走这里
            raise LLMError(f"调用大模型失败：{exc}") from exc

        if not response.choices:
            raise LLMError("大模型返回为空：choices 为空。")

        content = response.choices[0].message.content
        if not content:
            raise LLMError("大模型返回内容为空。")

        return content
