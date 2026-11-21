from travel_agent.config import is_placeholder


def test_is_placeholder() -> None:
    assert is_placeholder("sk-your-deepseek-key")
    assert is_placeholder("tvly-your-tavily-key")


def test_is_not_placeholder() -> None:
    assert not is_placeholder("sk-real-key")
    assert not is_placeholder(None)
