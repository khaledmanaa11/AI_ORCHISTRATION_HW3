# PROGRESS — single source of truth

NEXT: G1

> Each session: do the step named in NEXT, then move NEXT to the line below it.
> Legend: [ ] todo · [x] done · [~] in progress · [!] blocked.
> [HUMAN] steps are the Director's to run (money / live supervision) — agents STOP there.

## Part B — bootstrap (end-to-end smoke pipeline)
Triplet: [PRD](PRD_bootstrap.md) · [PLAN](PLAN_bootstrap.md) · [TODO](TODO_bootstrap.md) — approved 2026-06-10.

- [x] B0 — Skeleton scaffolded via `crewai create crew reasearch_crew`.
- [x] B1 — Repair `crew.py` imports (`os`, `LLM`/`Agent`/`Crew`/`Process`/`Task` from `crewai`, `load_dotenv`).
- [x] B2 — Pin model id to `openrouter/deepseek/deepseek-chat-v3.1:free`.
- [x] B3 — Externalize model / base_url / key-env-var name to config (§7.2).
- [x] B4 — Add `version.py` with `__version__ = "1.00"`; align `pyproject.toml` and `rate_limits.json`.
- [x] B5 — Add project-root `.gitignore` covering `.env *.key *.pem credentials.json` + `.env-example`.
- [x] B6 — Fix `pyproject.toml` line 8 version spec; verify `uv sync --frozen` reproduces.
- [x] B7 — Drop the `report.md` override; keep `output/paper.md`; ensure `output/` is created.
- [x] B8 — Unit tests for crew construction (mocked `LLM`), ≥85% coverage on `crew.py`.
- [x] B9 — Integration smoke test for kickoff → `output/paper.md` (mocked `LLM`).
- [ ] B10 — [HUMAN] Live end-to-end run with real `OPENROUTER_API_KEY`; paste first ~200 chars into commit.

## Part C — api_gatekeeper (single egress seam for all external API calls — §5.1)
Triplet: [PRD](PRD_api_gatekeeper.md) · [PLAN](PLAN_api_gatekeeper.md) · [TODO](TODO_api_gatekeeper.md) — TBDs locked 2026-06-10 with documented defaults; Director redlines before G1.

- [ ] G1 — Add `gateway/errors.py` + `gateway/__init__.py`: five-class exception hierarchy + provider→domain translator.
- [ ] G2 — Populate `config/rate_limits.json` with v1.00 schema (retry block + 3 providers); `uv add tenacity`.
- [ ] G3 — Add `gateway/rate_limiter.py`: token-bucket per provider, sleeps when burst exhausted.
- [ ] G4 — Add `gateway/retry.py`: tenacity policy, 3 retries on 429/5xx, no retry on 401/400.
- [ ] G5 — Add `gateway/telemetry.py`: Counters + snapshot / flush / reset.
- [ ] G6 — Add `gateway/http.py`: `http_post` wraps httpx with the same limiter/retry/telemetry/translate stack.
- [ ] G7 — Add `gateway/llm.py`: `GatekeptLLM(crewai.LLM)` overrides `.call` / `.completion`; `crew.py::_get_llm` returns `GatekeptLLM`.
- [ ] G8 — Update existing bootstrap tests for the subclass; add `gateway/` to coverage scope.
- [ ] G9 — Integration test: kickoff routes through gatekeeper (R-AC1).
- [ ] G10 — Update CLAUDE.md frozen invariant: no `litellm` / `anthropic` / raw `httpx` imports outside `gateway/`.
- [ ] G11 — [HUMAN] Live `uv run run_crew` with gateway; Director pastes `flush()` output into commit.

### Blocked steps
_(none yet)_
