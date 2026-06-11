import pytest

from reasearch_crew.crew import ReasearchCrew
from reasearch_crew.gateway import (
    config as gw_config,
    rate_limiter,
    telemetry,
)
from reasearch_crew.gateway.llm import GatekeptLLM


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    rate_limiter.reset()
    telemetry.reset()
    gw_config.reset_cache()
    monkeypatch.setattr(
        gw_config,
        "retry_policy",
        lambda: {"max_attempts": 3, "base_delay_sec": 0.0001, "jitter": "full"},
    )
    monkeypatch.setattr(rate_limiter.time, "sleep", lambda s: None)
    yield
    rate_limiter.reset()
    telemetry.reset()
    gw_config.reset_cache()


CANNED = (
    "# Abstract\n\nGateway-routed smoke test.\n\n"
    "## Conclusion\n\nAll calls flowed through GatekeptLLM.\n"
)


def test_kickoff_routes_through_gatekeeper(api_key, monkeypatch, tmp_path):
    """R-AC1: every LLM call in a kickoff is intercepted by GatekeptLLM."""
    monkeypatch.chdir(tmp_path)
    intercepted: list[int] = []

    original_call = GatekeptLLM.call

    def spy(self, messages, *a, **kw):
        intercepted.append(1)
        return original_call(self, messages, *a, **kw)

    monkeypatch.setattr(GatekeptLLM, "call", spy)

    from crewai import LLM

    def fake_base_call(self, *a, **kw):
        return {
            "choices": [{"message": CANNED}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 22},
        }

    monkeypatch.setattr(LLM, "call", fake_base_call)

    from crewai.agent import Agent

    def fake_execute(self, task, context=None, tools=None):
        self.llm.call([{"role": "user", "content": "x"}])
        return CANNED

    monkeypatch.setattr(Agent, "execute_task", fake_execute)

    ReasearchCrew().crew().kickoff(
        inputs={"topic": "Gateway Test", "current_year": "2026"}
    )

    assert len(intercepted) >= 1, "no LLM calls were routed through GatekeptLLM"

    snap = telemetry.snapshot()
    assert "gemini" in snap
    assert snap["gemini"]["calls"] == len(intercepted)
    assert snap["gemini"]["input_tokens"] == 11 * len(intercepted)
    assert snap["gemini"]["output_tokens"] == 22 * len(intercepted)


def test_get_llm_returns_gatekept_instance(api_key):
    from reasearch_crew.crew import _get_llm

    assert isinstance(_get_llm(), GatekeptLLM)
