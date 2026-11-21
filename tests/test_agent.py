from travel_agent.agent import (
    TravelAgent,
    parse_action,
    parse_finish,
    parse_tool_call,
    truncate_extra_pairs,
)


class ScriptedLLM:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = iter(outputs)

    def generate(self, prompt: str, system_prompt: str) -> str:
        return next(self.outputs)


def test_parse_action() -> None:
    text = 'Thought: 查天气\nAction: get_weather(city="武汉")'
    assert parse_action(text) == 'get_weather(city="武汉")'


def test_parse_tool_call() -> None:
    assert parse_tool_call('get_weather(city="武汉")') == (
        "get_weather",
        {"city": "武汉"},
    )


def test_parse_tool_call_rejects_extra_text() -> None:
    assert parse_tool_call('get_weather(city="武汉", bad)') is None


def test_parse_finish() -> None:
    assert parse_finish("Finish[去东湖]") == "去东湖"
    assert parse_finish("no") is None


def test_truncate_extra_pairs() -> None:
    text = 'Thought: a\nAction: get_weather(city="武汉")\nThought: b\nAction: Finish[x]'
    assert truncate_extra_pairs(text) == 'Thought: a\nAction: get_weather(city="武汉")'


def test_agent_runs_tool_then_finish() -> None:
    llm = ScriptedLLM(
        [
            'Thought: 先查天气\nAction: get_weather(city="武汉")',
            "Thought: 信息够了\nAction: Finish[去东湖]",
        ]
    )
    tools = {"get_weather": lambda city: f"{city}晴，20度"}
    agent = TravelAgent(llm, tools=tools, max_steps=3)

    assert agent.run("武汉天气") == "去东湖"
