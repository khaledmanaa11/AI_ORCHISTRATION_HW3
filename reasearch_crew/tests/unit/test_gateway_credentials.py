import pytest

from reasearch_crew.gateway.credentials import load_llm_config, resolve_key


def test_config_declares_three_phase_keys():
    assert load_llm_config()["key_envs"] == {
        "research": "GEMINI_API_KEY_RESEARCH",
        "compose": "GEMINI_API_KEY_COMPOSE",
        "typeset": "GEMINI_API_KEY_TYPESET",
    }


@pytest.mark.parametrize("phase", ["research", "compose", "typeset"])
def test_missing_phase_key_names_its_variable(phase):
    env_name = load_llm_config()["key_envs"][phase]
    with pytest.raises(RuntimeError, match=env_name):
        resolve_key(phase)


def test_optional_resolution_reports_missing_key():
    env_name = load_llm_config()["key_envs"]["typeset"]
    assert resolve_key("typeset", required=False) == (env_name, None)


def test_unknown_phase_is_rejected():
    with pytest.raises(ValueError, match="Unknown LLM credential phase"):
        resolve_key("unknown")
