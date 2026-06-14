# TODO — bootstrap

> Triplet: [PRD](PRD_bootstrap.md) · [PLAN](PLAN_bootstrap.md) · this
> Atomic steps in build order — each maps to PRD IDs. **One step = one commit = one /relay-next.**
> Every step has a Definition of Done (§2.2). When ready to build, copy these into `docs/PROGRESS.md`.

## Build order

- [x] **B0** — Skeleton scaffolded via `crewai create crew reasearch_crew`: package layout,
  `pyproject.toml`, `main.py`, `crew.py` (broken at HEAD — see B1), YAML configs, placeholder tool,
  local `.venv`. **DoD:** files present on disk. *(Done but not green — B1 closes the gap.)*

- [x] **B1** — Repair `crew.py` imports so the module actually loads. Add `import os`,
  `from crewai import LLM, Agent, Crew, Process, Task`, `from dotenv import load_dotenv`, and a
  `load_dotenv()` call at module top. (Satisfies FR-B3; **DoD:**
  `uv run python -c "from reasearch_crew.crew import ReasearchCrew"` exits 0.)

- [x] **B2** — Lock the OpenRouter model id. Replace the placeholder
  `openrouter/deepseek/deepseek-v4-pro` with `openrouter/deepseek/deepseek-chat-v3.1:free`
  (verified live on openrouter.ai, 2026-06-10). (Satisfies FR-B3; **DoD:** a one-shot
  `LLM(...).call("ping")` returns text without a 404 from OpenRouter.)

- [x] **B3** — Externalize model / base_url / key-env-var name to `config/llm.json` (or merge into
  `config/rate_limits.json` per §5.2). Replace inline strings in `crew.py` with config reads.
  (Satisfies FR-B3 & §7.2; **DoD:** grep finds zero hardcoded model / url / key strings in `src/`.)

- [x] **B4** — Add `src/reasearch_crew/version.py` with `__version__ = "1.00"`; mirror in
  `pyproject.toml` and the (future) `config/rate_limits.json`. (Satisfies §8.1; **DoD:** all three
  reads of "version" agree.)

- [x] **B5** — Add a project-root `.gitignore` covering `.env *.key *.pem credentials.json`, and
  add `.env-example` listing `OPENROUTER_API_KEY=` (blank value). (Satisfies §7.4; **DoD:**
  `git check-ignore .env` exits 0; `.env-example` is tracked.)

- [x] **B6** — Pin reproducibility. Fix `pyproject.toml` line 8
  (`"crewai[tools]==1.0.0,<2.0.0"` → `">=1.0.0,<2.0.0"`); confirm `uv.lock` is committed; a clean
  `uv sync --frozen` reproduces. (Satisfies FR-B4 & §8.4; **DoD:** `uv sync --frozen` exits 0 on a
  fresh checkout.)

- [x] **B7** — Resolve the `output_file` conflict — keep `output/paper.md` (per `tasks.yaml`) and
  drop the `output_file='report.md'` override in `crew.py:47`; ensure `output/` is created at
  runtime. (Satisfies FR-B5; **DoD:** a kickoff writes exactly `output/paper.md` and nothing else.)

- [x] **B8** — Unit tests: `tests/unit/test_crew_construction.py` patches `os.environ` for FR-B3 /
  R-AC2 and asserts agent role interpolation for R-AC3. **Must mock the `LLM` client — no live
  calls.** (Satisfies R-AC2 & R-AC3 §6.1; **DoD:** `uv run pytest -q` passes; coverage on
  `crew.py` ≥ 85%.)

- [x] **B9** — Integration test: `tests/integration/test_kickoff_smoke.py` runs
  `ReasearchCrew().crew().kickoff(inputs={...})` with a fake `LLM.call` returning canned text;
  asserts `output/paper.md` exists in a tmp dir and contains the abstract heading.
  (Satisfies R-AC1 §6.1; **DoD:** passes in CI, leaves no artifacts outside tmp.)

- [x] **B10** — `[HUMAN]` Live end-to-end run. SUPERSEDED by D1 (Gemini free tier replaced the
  flaky OpenRouter slugs) and closed by the real live run D15, which produced the actual
  Hebrew book rather than the bootstrap smoke `paper.md`. Agents STOP here — Director-run.

## Coverage matrix (§6 — every requirement has a test)

| Requirement | Step(s) | Test |
|---|---|---|
| FR-B1 | B8 | `tests/unit/test_crew_construction.py::test_agents_loaded_from_yaml` |
| FR-B2 | B8 | `tests/unit/test_crew_construction.py::test_tasks_loaded_from_yaml` |
| FR-B3 | B1, B2, B3, B8 | `tests/unit/test_crew_construction.py::test_llm_built_from_env` + integration B9 |
| FR-B4 | B6 | reproducibility gate (`uv sync --frozen`) — manual check item |
| FR-B5 | B7, B9 | `tests/integration/test_kickoff_smoke.py::test_paper_written_to_output_dir` |
| R-AC1 | B9 | `test_kickoff_smoke.py` |
| R-AC2 | B8 | `test_crew_construction.py::test_missing_key_raises` |
| R-AC3 | B8 | `test_crew_construction.py::test_role_interpolates_topic` |

## Locked decisions (Director approved 2026-06-10)

- **TBD-1 → LOCKED.** LLM provider is **OpenRouter** via CrewAI's `LLM` (which wraps `litellm`);
  the `anthropic` SDK is **not** used. CLAUDE.md "LLM provider" section updated accordingly.
- **TBD-2 → RE-LOCKED 2026-06-10 (post-live-attempt).** First lock was
  `openrouter/deepseek/deepseek-chat-v3.1:free`; the actual B10 run got a 404 from OpenRouter
  saying that slug is no longer free. Director picked **`openrouter/deepseek/deepseek-v4-pro`**
  as the working slug. Because B3 externalized model id to `config/llm.json`, the swap was a
  one-line config + two unit-test assertion updates — no `crew.py` change.
- **TBD-3 → LOCKED.** Output path is **`output/paper.md`** (per `tasks.yaml`). Step B7 drops the
  `output_file='report.md'` override at `crew.py:47`.
- **TBD-4 → LOCKED.** **Mocked-`LLM` tests only.** No `vcrpy` cassette. Rationale: §6 measures
  coverage of *our* logic, not the provider's; the live network is the Director's `[HUMAN]` step
  B10. Keeps CI fast and offline.
- **TBD-5 → LOCKED.** Next triplet after bootstrap is **`api_gatekeeper`** (Segal §5.1). No new
  agent, tool, or evaluator lands until the gatekeeper wraps `LLM` calls.

## Reminder

Once these `{TBD}`s are locked and the Director approves the triplet, `/relay-next` transcribes
these TODOs into code one step at a time, and `/relay-verify` holds each step to the Segal §19.1
Table-5 gate (`ruff` · `pytest` · cov ≥ 85% · ≤150 LOC/file · no hardcoded values · no secrets ·
`uv`-only) before it pushes.
