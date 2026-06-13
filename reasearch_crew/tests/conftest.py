import os

import pytest


@pytest.fixture(autouse=True)
def isolate_gemini_keys(monkeypatch):
    from reasearch_crew import crew as crew_mod

    for name in tuple(os.environ):
        if name.startswith("GEMINI_API_KEY"):
            monkeypatch.delenv(name, raising=False)
    crew_mod._llm_cache.clear()
    yield
    crew_mod._llm_cache.clear()


@pytest.fixture
def api_key(monkeypatch):
    from reasearch_crew.gateway import load_llm_config

    keys = {
        phase: f"test-{phase}-key"
        for phase in load_llm_config()["key_envs"]
    }
    for phase, value in keys.items():
        env_name = load_llm_config()["key_envs"][phase]
        monkeypatch.setenv(env_name, value)
    return keys
