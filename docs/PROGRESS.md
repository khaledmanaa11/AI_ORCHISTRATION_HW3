# PROGRESS — single source of truth

NEXT: B8

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
- [ ] B8 — Unit tests for crew construction (mocked `LLM`), ≥85% coverage on `crew.py`.
- [ ] B9 — Integration smoke test for kickoff → `output/paper.md` (mocked `LLM`).
- [ ] B10 — [HUMAN] Live end-to-end run with real `OPENROUTER_API_KEY`; paste first ~200 chars into commit.

### Blocked steps
_(none yet)_
