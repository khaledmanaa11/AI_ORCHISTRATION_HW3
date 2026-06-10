# PRD — bootstrap (end-to-end smoke pipeline)

> Triplet: this · [PLAN](PLAN_bootstrap.md) · [TODO](TODO_bootstrap.md)

| Field | Value |
|---|---|
| Component | bootstrap |
| Version | 1.00 |
| Depends on | (none — base layer) |

## 1. Description & theoretical background (§2.3)

The **bootstrap** is the minimal end-to-end CrewAI pipeline already scaffolded in
`src/reasearch_crew`: a two-agent sequential crew (**researcher → writer**) that takes a `{topic}`
input and emits a markdown paper to `output/paper.md`. Its job is **not** to produce a good
paper — its job is to prove the wiring is alive end-to-end: YAML-driven agent/task config, a
reachable LLM provider, CrewAI's `Process.sequential` runtime, and the file-output side effect.

Theoretically it is a degenerate orchestration: no planning loop, no tools, no reflection, no
critique — just a linear handoff from one agent's output into the next agent's context via
CrewAI's sequential `Process`. We accept that degeneracy on purpose. Every later mechanism (extra
agents, tool use, hierarchical process, evaluator) lands against a known-green bootstrap rail, so
when something breaks we know which seam owns the regression.

## 2. Inputs / Outputs / performance metrics (§2.3)

- **Input:** `inputs = {"topic": str, "current_year": str}` passed to `crew().kickoff(...)`.
  `topic` is non-empty free text; `current_year` is a 4-digit year string. The trigger variant
  (`run_with_trigger`) also accepts `crewai_trigger_payload: dict` parsed from `argv[1]`.
- **Output:** markdown file at `output/paper.md` (per `tasks.yaml`), roughly 1000 words, with an
  abstract, sections, and a conclusion, no fenced code wrapper. Verbose CrewAI trace on stdout.
- **Performance:** smoke-test scale only. A single kickoff completes in under ~5 min on the
  OpenRouter free DeepSeek tier; this is rate-limit constrained, not latency-tuned. No accuracy
  target (this is a wiring test, not a quality test).

## 3. Functional requirements

- **FR-B1** — Load the **researcher** and **writer** agents from `src/reasearch_crew/config/agents.yaml`, parameterised on `{topic}`.
- **FR-B2** — Load `research_task` and `writing_task` from `src/reasearch_crew/config/tasks.yaml` and wire them as `Process.sequential`.
- **FR-B3** — Use a single CrewAI `LLM` object pointed at OpenRouter's free-tier DeepSeek model; API key read from environment (`OPENROUTER_API_KEY`); `.env` loaded at import time.
- **FR-B4** — Expose the CLI entry points already declared in `pyproject.toml [project.scripts]`: `run_crew`, `train`, `replay`, `test`, `run_with_trigger`.
- **FR-B5** — Write the final paper to `output/paper.md`; create the directory if absent.

## 4. Constraints, limitations, alternatives considered (§2.3)

- **Provider = OpenRouter, model = free DeepSeek tier** (not Anthropic direct).
  · Alternative rejected: Anthropic direct — pricier and the assignment allows any provider as long
  as it sits behind the gatekeeper; the free OpenRouter tier removes the rate-limit-vs-cost squeeze
  on early iteration. CLAUDE.md's "Anthropic Claude via `anthropic` SDK" line must be updated to
  reflect this (see TBD-1 in the TODO).
- **No tools, no memory, no hierarchical process** in the bootstrap.
  · Alternative rejected: tool-equipped researcher (web search) — deferred until the wiring is
  proven, so the smoke test can never fail for a tool-side reason.
- **YAML-driven agent/task config** (CrewAI convention).
  · Alternative rejected: in-code `Agent(role=…)` definitions — they couple prompt iteration to
  orchestration code and make diffs noisier.
- **Single shared `LLM` instance for both agents**.
  · Alternative rejected: per-agent LLMs — premature, the bootstrap exists to prove one model works.

## 5. Success criteria & test scenarios (§2.3)

- **R-AC1** — `uv run run_crew` completes with exit 0 and writes `output/paper.md` containing an
  abstract section. → test scenario: integration test with the LLM client mocked, asserts that
  `kickoff(...)` returns and writes the file.
- **R-AC2** — `ReasearchCrew()` instantiates without raising when `OPENROUTER_API_KEY` is set, and
  raises a clear error when it is absent. → test scenario: unit test that patches `os.environ`.
- **R-AC3** — Agent roles in `agents.yaml` interpolate `{topic}` from `inputs`. → test scenario:
  unit test that calls `ReasearchCrew().crew()` with a fixed topic and asserts the rendered role
  string for the researcher.

## Non-goals

- Quality of the produced paper (no evaluator, no rubric).
- Cost optimization (free tier; rate-limit constrained).
- Multi-provider support / model fallback.
- Tool use, memory, hierarchical process — all deferred to later triplets.
- Production-grade error recovery (retries, circuit breakers, partial-output handling).
