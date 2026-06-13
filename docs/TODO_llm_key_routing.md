# TODO - llm_key_routing

> Triplet: [PRD](PRD_llm_key_routing.md) - [PLAN](PLAN_llm_key_routing.md) - this

## Build order

- [x] **D18 - Route the pipeline through three Gemini keys.**
  Add the config-driven gateway credential resolver; bind the Researcher, composer,
  Typesetter, and cover generation to the phases defined in the approved plan. Remove
  runtime dependence on the shared `GEMINI_API_KEY`. Preserve the current model and all
  gateway behavior. Update tests and setup/run documentation.

  **Definition of Done:**
  - Three distinct fake keys reach the intended phases in unit tests.
  - Missing phase keys fail clearly; cover alone keeps its documented image fallback.
  - Tests cannot inherit live Gemini values from `.env`.
  - The full mocked pipeline remains green and makes no live API call.
  - `.env-example` and D15 instructions list all three keys.
  - `uv run ruff check src tests` reports zero errors.
  - `uv run pytest -q` reports zero failures.
  - `uv run pytest --cov` reports at least 85% coverage.
  - Every source and test file is at most 150 code lines.
  - No secret, hardcoded key-env name, gateway bypass, or unrelated model change is
    introduced.

## Current audit

- The worktree already contains an incomplete attempt in `llm.json`, `crew.py`,
  `main.py`, and construction tests.
- Cover generation and project documentation still use the retired shared key.
- The current test gate is red because a routing test inherits a real Researcher value
  loaded from `.env` instead of isolating the environment.
- These existing edits must be preserved and completed, not reverted wholesale.
