"""命令行入口。"""

from __future__ import annotations

import argparse
import logging

from . import __version__
from .agent import TravelAgent
from .config import ConfigError, Settings
from .llm import LLMError, OpenAICompatibleClient

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="travel-agent",
        description="一个用于学习 ReAct 的最小旅行助手。",
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="用户问题；不填则使用 .env 中的 USER_PROMPT。",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="最大 ReAct 循环次数；默认读取 AGENT_MAX_STEPS。",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="输出调试日志。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    if not args.verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        logger.error("启动失败：%s", exc)
        return 2

    question = " ".join(args.question).strip() or settings.user_prompt

    try:
        llm = OpenAICompatibleClient(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=settings.llm_timeout,
        )
    except LLMError as exc:
        logger.error("启动失败：%s", exc)
        return 2

    agent = TravelAgent(
        llm,
        max_steps=args.max_steps or settings.max_steps,
    )
    answer = agent.run(question)

    if answer is None:
        return 1

    logger.info("任务完成，最终答案: %s", answer)
    return 0
