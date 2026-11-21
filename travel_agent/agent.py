"""ReAct 循环与 Action 解析。"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from .llm import LLMError
from .prompts import AGENT_SYSTEM_PROMPT
from .tools import available_tools

logger = logging.getLogger(__name__)

Tool = Callable[..., str]


class LLMClient(Protocol):
    """Agent 只依赖 generate 这一个方法，方便测试时替换成假模型。"""

    def generate(self, prompt: str, system_prompt: str) -> str: ...


def truncate_extra_pairs(text: str) -> str:
    """只保留第一组 Thought/Action，避免模型一次输出多轮。"""
    match = re.search(
        r"(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return text.strip()

    truncated = match.group(1).strip()
    if truncated != text.strip():
        logger.info("已截断多余的 Thought-Action 对")
    return truncated


def parse_action(text: str) -> str | None:
    """提取单行 Action。系统提示要求 Action 必须写在同一行。"""
    match = re.search(r"^\s*Action:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_finish(action: str) -> str | None:
    match = re.fullmatch(r"Finish\[(.*)\]", action, re.DOTALL)
    return match.group(1).strip() if match else None


def parse_tool_call(action: str) -> tuple[str, dict[str, Any]] | None:
    """把 get_weather(city="武汉") 解析成 ("get_weather", {"city": "武汉"})。"""
    match = re.fullmatch(r"(\w+)\((.*)\)", action, re.DOTALL)
    if not match:
        return None

    tool_name, args_text = match.group(1), match.group(2).strip()
    kwargs: dict[str, Any] = {}

    if args_text:
        pattern = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
        kwargs = dict(pattern.findall(args_text))
        # 去掉已解析的 key="value" 和逗号后，如果还有残留，说明参数格式不对。
        remaining = pattern.sub("", args_text).replace(",", "").strip()
        if remaining:
            return None

    return tool_name, kwargs


class TravelAgent:
    """一个最小可用的 ReAct Agent。"""

    def __init__(
        self,
        llm: LLMClient,
        tools: Mapping[str, Tool] | None = None,
        max_steps: int = 5,
        system_prompt: str = AGENT_SYSTEM_PROMPT,
    ) -> None:
        self.llm = llm
        self.tools = dict(tools or available_tools)
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    def run(self, user_prompt: str) -> str | None:
        """执行 ReAct 循环；成功返回最终答案，失败返回 None。"""
        history = [f"用户请求: {user_prompt}"]
        logger.info("用户输入: %s", user_prompt)
        logger.info("=" * 40)

        for step in range(1, self.max_steps + 1):
            logger.info("--- 循环 %s ---", step)

            try:
                output = self.llm.generate(
                    "\n".join(history),
                    system_prompt=self.system_prompt,
                )
            except LLMError as exc:
                logger.error("任务终止：%s", exc)
                return None

            output = truncate_extra_pairs(output)
            logger.info("模型输出:\n%s", output)
            history.append(output)

            action = parse_action(output)
            if action is None:
                self._observe(
                    history,
                    "错误: 未能解析到 Action 字段。"
                    "请严格使用 'Thought: ... Action: ...' 格式。",
                )
                continue

            final_answer = parse_finish(action)
            if final_answer is not None:
                return final_answer

            parsed = parse_tool_call(action)
            if parsed is None:
                self._observe(
                    history,
                    '错误: Action 格式不对。'
                    '应为 function_name(arg="value") 或 Finish[最终答案]。',
                )
                continue

            tool_name, kwargs = parsed
            tool = self.tools.get(tool_name)

            if tool is None:
                self._observe(
                    history,
                    f"错误:未定义的工具 '{tool_name}'。"
                    f"可用工具: {', '.join(self.tools)}",
                )
                continue

            try:
                observation = tool(**kwargs)
            except TypeError as exc:
                observation = f"错误:工具 {tool_name} 的参数不匹配 - {exc}"
            except Exception as exc:  # noqa: BLE001 - 工具边界统一转成 Observation
                observation = f"错误:工具 {tool_name} 执行失败 - {exc}"

            self._observe(history, observation)

        logger.warning("达到最大循环次数（%s），任务未完成。", self.max_steps)
        return None

    @staticmethod
    def _observe(history: list[str], message: str) -> None:
        observation = f"Observation: {message}"
        history.append(observation)
        logger.info("%s", observation)
        logger.info("=" * 40)
