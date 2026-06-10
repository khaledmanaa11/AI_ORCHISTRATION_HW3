import pytest


@pytest.fixture(autouse=True)
def reset_llm_singleton():
    from reasearch_crew import crew as crew_mod

    crew_mod._llm_singleton = None
    yield
    crew_mod._llm_singleton = None


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-xyz")
