import pytest

from reasearch_crew.crew import ReasearchCrew, _get_llm
from reasearch_crew.gateway import load_llm_config


def test_load_llm_config_returns_pinned_model():
    cfg = load_llm_config()
    assert cfg["model"] == "gemini/gemini-2.5-flash"
    assert cfg["base_url"] == ""
    assert cfg["version"] == "1.00"


def test_phase_llms_are_routed_and_cached(api_key):
    crew_obj = ReasearchCrew()
    llms = {
        "research": crew_obj.researcher().llm,
        "compose": crew_obj.get_llm("compose"),
        "typeset": crew_obj.typesetter().llm,
    }
    assert {phase: llm.api_key for phase, llm in llms.items()} == api_key
    assert len({id(llm) for llm in llms.values()}) == 3
    assert _get_llm("compose") is llms["compose"]
    llm_obj = llms["research"]
    assert llm_obj.model == "gemini/gemini-2.5-flash"


def test_missing_phase_key_raises(monkeypatch):
    cfg = load_llm_config()
    env_name = cfg["key_envs"]["research"]
    monkeypatch.delenv(env_name, raising=False)
    with pytest.raises(RuntimeError, match=env_name):
        _get_llm("research")


def test_agents_loaded_from_yaml(api_key):
    crew_obj = ReasearchCrew().crew()
    roles = " ".join(a.role for a in crew_obj.agents)
    assert "Research" in roles     # the researcher
    assert "Typesetter" in roles   # the typesetter
    # authoring is now handled by compose_book (D16), not a crew agent
    assert len(crew_obj.agents) == 2


def test_tasks_loaded_from_yaml(api_key):
    crew_obj = ReasearchCrew().crew()
    output_files = {t.output_file for t in crew_obj.tasks}
    assert "output/research.md" in output_files
    # writing_task removed; book.he.md is written by compose_book (D16)
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
