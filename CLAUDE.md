# Orchestration AI — HW3 — standing rules (Segal V3; auto-loaded, never re-explain)

Full standard: `docs/SEGAL_GUIDELINES_V3.md`. These are the enforced essentials.

## Roles (Segal §1.4 — orchestration IS the method)
- **Director** (human): says "next", hands prompts to the Developer, pastes commit hashes back.
- **Orchestrator** (this chat + relay-* skills): `/relay-next` emits the next Developer Prompt;
  `/relay-verify` runs the gate and pushes. Writes NO feature code.
- **Developer** (a SEPARATE session): implements one step, commits locally (NO push), returns hash.
- **First rule of pro AI coding:** full requirements + docs BEFORE any code. Approve every PRD/PLAN/
  TODO before development (§2.5). One atomic step per session; never start a `[HUMAN]` step.

## Source of truth
`docs/PROGRESS.md` is the ONLY status surface; its `NEXT:` line names the one step in play.

## The Gate — every step must pass before push (Segal §19.1 Table 5)
```
uv run ruff check src tests        # 0 errors (§7.1)
uv run pytest -q                   # 0 failures (§6.1 TDD)
uv run pytest --cov                # ≥ 85% (§6.2)
```
Plus, verified by reading the diff:
- Every source AND test file ≤ 150 code lines (§3.2) — split, don't compress.
- 0 hardcoded host/port/timeout/url/model/key — all from config/env (§7.2).
- All external API calls go through the API Gatekeeper (§5.1); rate limits from config (§5.2).
- All business logic reachable via the SDK layer (§4.1); no duplication — mixin/base (§4.2).
- No secrets in code; `.env-example` present; `.gitignore` covers `.env *.key *.pem credentials.json` (§7.4).
- Everything runs through `uv` — no `pip`/`python -m`/`venv` (§8.4).
- Version starts at 1.00 in `version.py`, JSON `version`, `rate_limits.version` (§8.1).
- {PROJECT FROZEN INVARIANT — none yet; once a `protocol/` or frozen module exists, name it here,
  e.g. "do not edit src/hw3/protocol/; PROTOCOL_VERSION stays \"1.00\""}

## Commit voice (§8.2)
Conversational, like someone sat with us. One logical step per commit. End every commit:
```
Co-Authored-By: Khaled <khaled.mnaa43@gmail.com>
```
Only the Orchestrator pushes, only after the gate is green.

## LLM provider
OpenRouter via CrewAI's `LLM` class (which wraps `litellm`); free-tier DeepSeek model
`openrouter/deepseek/deepseek-chat-v3.1:free`; API key is `OPENROUTER_API_KEY` loaded from `.env`.
Rate limits, not cost, are the constraint (free tier is rate-capped; cost ≈ $0). Tests always mock
the client — no test touches the live API. Token-cost analysis required at submission (§11);
report tokens in/out even though dollar cost is zero.
