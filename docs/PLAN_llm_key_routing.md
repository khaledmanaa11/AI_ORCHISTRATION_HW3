# PLAN - llm_key_routing

> Triplet: [PRD](PRD_llm_key_routing.md) - this - [TODO](TODO_llm_key_routing.md)

## Architecture

```text
config/llm.json
  key_envs.research -> GEMINI_API_KEY_RESEARCH
  key_envs.compose  -> GEMINI_API_KEY_COMPOSE
  key_envs.typeset  -> GEMINI_API_KEY_TYPESET
             |
             v
gateway credential resolver
  resolve_key("research" | "compose" | "typeset")
       |                 |                 |
       v                 v                 v
Researcher          compose_book       Typesetter
GatekeptLLM         GatekeptLLM         GatekeptLLM
                                          |
                                          +-> cover gateway request
```

The resolver owns config loading, phase validation, and environment lookup. Callers ask
for a phase; they do not know environment-variable names. LLM instances are cached by
phase so keys cannot be shared accidentally.

## File changes

- `src/reasearch_crew/config/llm.json`
  - Replace the shared `api_key_env` contract with `key_envs` for the three phases.
  - Preserve the current model and base URL.
- `src/reasearch_crew/gateway/credentials.py`
  - Load the LLM credential mapping and resolve a phase key.
  - Return both env name and value where diagnostics need the name.
- `src/reasearch_crew/gateway/__init__.py`
  - Export the credential resolver.
- `src/reasearch_crew/crew.py`
  - Build/cache one `GatekeptLLM` per phase using the resolver.
  - Bind Researcher and Typesetter explicitly; expose the composer LLM explicitly.
- `src/reasearch_crew/main.py`
  - Request the compose phase LLM without embedding env names.
- `src/reasearch_crew/report/cover.py`
  - Resolve the typeset credential and retain the bundled-image fallback.
- Tests
  - Isolate all key env vars in the autouse fixture.
  - Cover exact phase routing, missing keys, cache separation, cover routing, and the
    full mocked pipeline.
- Documentation
  - Replace the single-key setup/run instructions with all three variables.

## Decisions

- **ADR-K1 - Three required LLM phase keys.**
  Silent fallback to one shared key is rejected because it recreates the quota failure
  this feature exists to prevent.
- **ADR-K2 - Typeset key owns cover generation.**
  Cover generation is part of final artifact production and runs immediately before the
  Typesetter phase. A fourth key is outside the requested contract.
- **ADR-K3 - Credential lookup belongs beside the gateway.**
  Both LLM and image egress need the same mapping. A shared gateway helper avoids
  duplicated env access and keeps external-call credentials centralized.
- **ADR-K4 - Tests clear inherited dotenv values.**
  Every key-routing test must be deterministic even when the local `.env` contains real
  phase keys.

## Verification

```powershell
uv run ruff check src tests
uv run pytest -q
uv run pytest --cov
```

Diff review also checks all Python/test files are at most 150 code lines, no secret is
committed, no external call bypasses `gateway/`, and the configured model is unchanged.
