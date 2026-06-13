from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "llm.json"


def load_llm_config() -> dict:
    """Load the model and phase credential mapping from llm.json."""
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_key(
    phase: str, *, required: bool = True
) -> tuple[str, str | None]:
    """Resolve only the credential assigned to an LLM pipeline phase."""
    key_envs = load_llm_config()["key_envs"]
    try:
        env_name = key_envs[phase]
    except KeyError as exc:
        raise ValueError(f"Unknown LLM credential phase: {phase}") from exc

    value = os.getenv(env_name)
    if required and not value:
        raise RuntimeError(f"Missing environment variable: {env_name}")
    return env_name, value
