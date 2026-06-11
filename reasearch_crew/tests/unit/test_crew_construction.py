import pytest

from reasearch_crew.crew import ReasearchCrew, _get_llm, _load_llm_config


def test_load_llm_config_returns_pinned_model():
    cfg = _load_llm_config()
    assert cfg["model"] == "gemini/gemini-2.0-flash"
    assert cfg["base_url"] == ""
    assert cfg["api_key_env"] == "GEMINI_API_KEY"
    assert cfg["version"] == "1.00"


def test_llm_built_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "sk-test-12345")
    llm_obj = _get_llm()
    assert llm_obj.api_key == "sk-test-12345"
    assert llm_obj.model == "gemini/gemini-2.0-flash"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        _get_llm()


def test_get_llm_is_cached(api_key):
    first = _get_llm()
    second = _get_llm()
    assert first is second


def test_agents_loaded_from_yaml(api_key):
    crew_obj = ReasearchCrew().crew()
    roles = " ".join(a.role for a in crew_obj.agents)
    assert "Research" in roles
    assert "Writer" in roles
    assert len(crew_obj.agents) == 2


def test_tasks_loaded_from_yaml(api_key):
    crew_obj = ReasearchCrew().crew()
    descs = " ".join(t.description for t in crew_obj.tasks)
    assert "research" in descs.lower()
    assert "paper" in descs.lower()
    assert len(crew_obj.tasks) == 2


def test_role_interpolates_topic(api_key):
    crew_obj = ReasearchCrew().crew()
    researcher = next(a for a in crew_obj.agents if "Research" in a.role)
    assert "{topic}" in researcher.role
    researcher.interpolate_inputs({"topic": "Quantum Computing"})
    assert "Quantum Computing" in researcher.role
    assert "{topic}" not in researcher.role


def test_crew_uses_sequential_process(api_key):
    from crewai import Process

    crew_obj = ReasearchCrew().crew()
    assert crew_obj.process == Process.sequential
