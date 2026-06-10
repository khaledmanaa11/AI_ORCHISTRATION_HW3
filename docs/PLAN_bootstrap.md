# PLAN — bootstrap

> Triplet: [PRD](PRD_bootstrap.md) · this · [TODO](TODO_bootstrap.md)

## Architecture (the seam)

```
            inputs = {topic, current_year}
                       │
                       ▼
   ┌────────────────────────────────────────┐
   │ main.py  (run / train / replay / test) │   CLI entry points
   └──────────────────┬─────────────────────┘
                      │ kickoff(inputs)
                      ▼
   ┌────────────────────────────────────────┐
   │ crew.py :: ReasearchCrew               │
   │   @CrewBase                            │
   │   ├── @agent researcher                │
   │   ├── @agent writer                    │
   │   ├── @task  research_task             │
   │   ├── @task  writing_task              │
   │   └── @crew  crew (Process.sequential) │
   └──────────────────┬─────────────────────┘
                      │ uses (shared)
                      ▼
   ┌────────────────────────────────────────┐
   │ LLM(openrouter/deepseek/<free model>)  │   single shared LLM object
   └──────────────────┬─────────────────────┘
                      │ HTTP
                      ▼
                  OpenRouter
                      │
                      ▼
               output/paper.md
```

Behind-the-SDK-layer (§4.1): all model traffic flows through CrewAI's `LLM` class, which itself
wraps `litellm`. The OpenRouter HTTP boundary is therefore the **only** API edge — the future
gatekeeper will sit in front of `LLM` calls, not inside agent code.

## Public interface (stable contract)

- `ReasearchCrew()` — no-args constructor.
- `ReasearchCrew().crew()` → CrewAI `Crew` instance.
- `ReasearchCrew().crew().kickoff(inputs: dict[str, str])` → `CrewOutput`.
- CLI scripts exactly as declared in `pyproject.toml [project.scripts]`.

These are what later components (evaluator, additional agents, gatekeeper) are allowed to depend
on. The internals of `crew.py` are not part of the contract.

## File layout (each ≤ 150 code lines, §3.2)

- `src/reasearch_crew/main.py` — CLI entry points only, no business logic.
- `src/reasearch_crew/crew.py` — `ReasearchCrew` class, agent/task/crew declarations, LLM construction.
- `src/reasearch_crew/config/agents.yaml` — researcher + writer prompts.
- `src/reasearch_crew/config/tasks.yaml` — research_task + writing_task descriptions.
- `src/reasearch_crew/tools/custom_tool.py` — placeholder (unused in bootstrap; left for later triplets).
- `src/reasearch_crew/version.py` — `__version__ = "1.00"` (§8.1; **to be added**).
- `config/llm.json` (or merged into `config/rate_limits.json`, §5.2) — model id, base_url, key-env-var name (**to be added**, replaces hardcoded strings in `crew.py`).
- `.env` (gitignored) — `OPENROUTER_API_KEY`.
- `.env-example` — same key, blank value (§7.4; **to be added**).
- `pyproject.toml` — entry points, version pin (line 8 currently malformed; fix in TODO B6).

## ADRs (decision + rationale + alternative)

- **ADR-B1 — LLM provider is OpenRouter (free DeepSeek).**
  · Rationale: free tier removes the cost/rate squeeze on early smoke runs; provider switch later
  only touches the `LLM(...)` line in `crew.py` once the config refactor lands.
  · Rejected: Anthropic direct (cost), Ollama local (no GPU on the Director's machine).
- **ADR-B2 — `Process.sequential` over `Process.hierarchical`.**
  · Rationale: simplest possible flow proves the wiring end-to-end; hierarchical adds a manager
  agent and a planning step that we don't need yet.
  · Rejected: hierarchical (premature complexity).
- **ADR-B3 — YAML-driven agent and task config.**
  · Rationale: CrewAI convention; prompts iterate without touching Python.
  · Rejected: hard-coded `Agent(role=...)` in Python (mixes prompt and orchestration in diffs).
- **ADR-B4 — Single shared `LLM` instance for both agents.**
  · Rationale: bootstrap; per-agent models is a later optimization driven by cost or capability
  asymmetry that we don't yet observe.
  · Rejected: per-agent LLMs.

## Concurrency / gatekeeper / config notes

- **Concurrency:** none — `Process.sequential`, single kickoff per invocation. Section 15
  concerns do not apply yet.
- **Gatekeeper (§5.1):** **not yet introduced.** The bootstrap calls `LLM(...)` directly. This PRD
  acknowledges that as a known gap; the immediate follow-up triplet `api_gatekeeper` is expected
  to wrap `LLM` and is mandated by Segal §5.1 before any further mechanism lands.
- **Config (§7.2):** model id, base_url, and the api-key environment-variable **name** must come
  from a config object, not from inline strings in `crew.py`. The current code hardcodes the model
  id (`openrouter/deepseek/deepseek-v4-pro`) and the base URL — the biggest §7.2 violation the
  bootstrap closes in its own TODO (step B3).
- **Secrets (§7.4):** `.env-example` and a `.gitignore` covering `.env *.key *.pem credentials.json`
  are required. Currently only the package-level `src/reasearch_crew/.gitignore` exists; project
  root `.gitignore` and `.env-example` must be added (TODO B5).
- **Versioning (§8.1):** `version.py`, the JSON `version`, and `pyproject.toml` must all read
  `1.00` and agree (TODO B4).
