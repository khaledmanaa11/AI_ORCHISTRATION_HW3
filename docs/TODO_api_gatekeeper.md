# TODO — api_gatekeeper

> Triplet: [PRD](PRD_api_gatekeeper.md) · [PLAN](PLAN_api_gatekeeper.md) · this
> Atomic steps in build order — each maps to PRD IDs. **One step = one commit = one /relay-next.**
> Every step has a Definition of Done (§2.2). When ready to build, copy these into `docs/PROGRESS.md`.

## Build order

- [x] **G1** — Add `src/reasearch_crew/gateway/errors.py`: five-class hierarchy
  (`GatewayError`, `RateLimitExceeded`, `ProviderUnavailable`, `AuthError`,
  `BadRequest`) and `from_provider_exception(exc)` translator that maps litellm /
  httpx exceptions to the right subclass. Also add `gateway/__init__.py` re-exporting
  the five classes. (Satisfies FR-G4; **DoD:** `tests/unit/test_gateway_errors.py`
  covers every translation branch with ≥ 95% line cov on `errors.py`.)

- [x] **G2** — Populate `src/reasearch_crew/config/rate_limits.json` with the v1.00
  schema (retry block + 3 provider entries: `openrouter`, `anthropic`, `serper`).
  Add `tenacity` as a direct dep via `uv add tenacity`. (Satisfies FR-G2; **DoD:**
  `uv run python -c "import json; print(json.load(open('src/reasearch_crew/config/rate_limits.json'))['providers']['openrouter']['rpm'])"`
  prints a positive int; `tenacity` resolves in `uv.lock`.)

- [x] **G3** — Add `src/reasearch_crew/gateway/rate_limiter.py`: per-provider
  token-bucket `acquire(provider)` that reads from `rate_limits.json` on first use,
  sleeps the calling thread when burst exhausted. Module-level singleton. (Satisfies
  FR-G2; **DoD:** `tests/unit/test_gateway_rate_limiter.py` with monkey-patched
  `time.sleep` proves R-AC3: two calls at 1 RPS sleeps ≈ 1s.)

- [x] **G4** — Add `src/reasearch_crew/gateway/retry.py`: `tenacity`-built retry
  policy factory. Retries on `RateLimitExceeded`, `ProviderUnavailable`, and the
  underlying `litellm.RateLimitError` / `httpx.HTTPStatusError` for 429/5xx. Does
  NOT retry on `AuthError`, `BadRequest`. Max attempts + base delay read from
  `rate_limits.json`. (Satisfies FR-G3; **DoD:** `tests/unit/test_gateway_retry.py`
  proves R-AC2 — 3 retries on a 429, 4th raises `RateLimitExceeded`; AuthError raises
  immediately with attempt count = 1.)

- [x] **G5** — Add `src/reasearch_crew/gateway/telemetry.py`: `Counters` dataclass
  (calls, retries, input_tokens, output_tokens) + module registry, with
  `snapshot()`, `flush()`, `reset()`. (Satisfies FR-G5; **DoD:**
  `tests/unit/test_gateway_telemetry.py` proves R-AC5 — counters increment per call,
  per provider; snapshot returns correct totals; reset clears.)

- [x] **G6** — Add `src/reasearch_crew/gateway/http.py`: `http_post(url, headers,
  json, *, provider)` that wraps `httpx.post` with the same rate-limiter → retry →
  telemetry → error-translation stack. (Satisfies FR-G6; **DoD:**
  `tests/unit/test_gateway_http.py` with httpx mock proves R-AC4 — 1 RPS provider
  spaces calls ≈ 1s apart; 401 raises `AuthError` without retry; 503 retries.)

- [x] **G7** — Add `src/reasearch_crew/gateway/llm.py`: `GatekeptLLM(crewai.LLM)`.
  Override `.call(messages, **kw)` to run inside the limiter/retry/telemetry stack;
  override `.completion(...)` similarly. Also update `crew.py`'s `_get_llm` to
  return `GatekeptLLM` instead of `LLM`. (Satisfies FR-G1; **DoD:**
  `tests/unit/test_gateway_llm.py` proves `.call` increments telemetry, retries on
  429, translates a 401 to `AuthError`; existing bootstrap test
  `test_llm_built_from_env` still passes against the subclass.)

- [x] **G8** — Touch up bootstrap tests for the new return type. The B8 assertion
  `llm_obj.model == "openrouter/google/gemma-4-31b-it:free"` still holds because
  `GatekeptLLM` inherits `.model`; verify and amend if needed. Also gate the new
  `gateway/` package in the coverage scope (`[tool.coverage.run] source` includes
  `src/reasearch_crew/gateway/`). (Satisfies no FR but is the §6.2 gate hygiene;
  **DoD:** `uv run pytest -q` green; project coverage ≥ 85%.)

- [x] **G9** — Add `tests/integration/test_gateway_in_crew.py`: kickoff with mocked
  `litellm.completion` + the gateway spy fixture, asserts every LLM call went through
  `GatekeptLLM.call` (R-AC1) and telemetry shows the right per-provider totals.
  (Satisfies R-AC1; **DoD:** test passes; coverage on `gateway/` ≥ 85%.)

- [x] **G10** — Update `CLAUDE.md` "Project frozen invariant" line: add **"all
  external API calls go through `src/reasearch_crew/gateway/`; importing `litellm`,
  `anthropic`, or raw `httpx`/`requests` outside `gateway/` is a §5.1 violation."**
  Add a `.gitignore` rule for any telemetry log file the future flush sink writes.
  (Satisfies the §5.1 lock that makes the gatekeeper *enforceable*; **DoD:** grep
  outside `gateway/` for `import litellm`, `import anthropic`, `import requests`,
  raw `httpx.` → zero hits.)

- [ ] **G11** — `[HUMAN]` One live end-to-end run of `uv run run_crew` with the
  gateway in place. Director eyeballs the post-kickoff `flush()` output: per-provider
  call count + token totals + (if 429 occurred) retry count. (**DoD:** Director pastes
  the flush output into the commit / PR description.)

## Coverage matrix (§6 — every requirement has a test)

| Requirement | Step(s) | Test |
|---|---|---|
| FR-G1 | G7, G9 | `tests/integration/test_gateway_in_crew.py::test_kickoff_routes_through_gatekeeper` |
| FR-G2 | G2, G3 | `tests/unit/test_gateway_rate_limiter.py::test_config_loaded_from_json` |
| FR-G3 | G4 | `tests/unit/test_gateway_retry.py::test_three_retries_then_raise` |
| FR-G4 | G1 | `tests/unit/test_gateway_errors.py::test_translation_table` |
| FR-G5 | G5 | `tests/unit/test_gateway_telemetry.py::test_snapshot_matches_calls` |
| FR-G6 | G6 | `tests/unit/test_gateway_http.py::test_http_post_respects_rate_limit` |
| R-AC1 | G9 | `test_gateway_in_crew.py::test_kickoff_routes_through_gatekeeper` |
| R-AC2 | G4 | `test_gateway_retry.py::test_three_retries_then_raise` |
| R-AC3 | G3 | `test_gateway_rate_limiter.py::test_token_bucket_sleeps_when_empty` |
| R-AC4 | G6 | `test_gateway_http.py::test_http_post_respects_rate_limit` |
| R-AC5 | G5, G9 | `test_gateway_telemetry.py::test_snapshot_matches_calls` |

## Locked decisions (defaults applied 2026-06-10 — Director may redline before G1)

- **TBD-G1 → LOCKED.** Rate limits as proposed: `openrouter rpm=20, burst=5`;
  `anthropic rpm=50, tpm=40000, burst=10`; `serper rpm=60, burst=5`. Conservative
  starts that match the providers' published free / tier-1 caps. **Tunable from
  `config/rate_limits.json` without code change** — Director redlines the numbers
  in G2's JSON edit if real limits differ.
- **TBD-G2 → LOCKED.** Telemetry sink is **stdout only** for v1.00 (`flush()` prints
  a one-line summary per provider after kickoff). A JSON file sink is deferred to a
  later observability triplet — out of scope here.
- **TBD-G3 → LOCKED.** **Sequential only** — no `threading.Lock` in the limiter for
  v1.00, because CrewAI runs `Process.sequential`. When `Process.hierarchical` lands
  in a future triplet, that triplet adds the lock (a ~30-line change isolated to
  `rate_limiter.py`).
- **TBD-G4 → LOCKED.** Retries emit **one-line WARN logs** via stdlib `logging`
  (silent retries hide real problems). Format: `"gateway: retry attempt N for
  <provider>: <reason>"`. No structured logging dep added.

## Reminder

Once these TBDs are locked and you approve the triplet, `/relay-next` transcribes
these TODOs into code one step at a time, and `/relay-verify` holds each step to the
Segal §19.1 Table-5 gate (`ruff` · `pytest` · cov ≥ 85% · ≤150 LOC/file · no
hardcoded values · no secrets · `uv`-only) before it pushes. The B-bootstrap commits
showed this rhythm — same drum for G.
