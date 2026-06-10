# PLAN — api_gatekeeper

> Triplet: [PRD](PRD_api_gatekeeper.md) · this · [TODO](TODO_api_gatekeeper.md)

## Architecture (the seam)

```
                        Agent.execute_task
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ crewai.LLM API surface (call, completion)  │
        └──────────────────┬─────────────────────────┘
                           │  (subclassed)
                           ▼
        ┌────────────────────────────────────────────┐
        │ GatekeptLLM         (gateway/llm.py)       │
        │   .call(messages) →                         │
        │     rate_limiter.acquire(provider)          │
        │     retry_policy.run(                       │
        │       litellm completion call               │
        │     ) → translate_errors() → telemetry()    │
        └──────────────────┬─────────────────────────┘
                           │  HTTP
                           ▼
                     OpenRouter / Anthropic


        SerperDevTool (or future HTTP tool)
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │ gateway.http_post(url, …, provider=…)      │
        │   (gateway/http.py)                         │
        │   same rate_limiter / retry / telemetry    │
        └──────────────────┬─────────────────────────┘
                           │  HTTP
                           ▼
                          Serper.dev
```

All external egress narrows to two functions: `GatekeptLLM.call` and `http_post`.
The rate limiter, retry policy, telemetry, and exception map are shared singletons
(module-level), constructed from `config/rate_limits.json` on first use.

## Public interface (stable contract)

```python
# src/reasearch_crew/gateway/__init__.py
from .llm import GatekeptLLM
from .http import http_post
from .errors import (
    GatewayError, RateLimitExceeded,
    ProviderUnavailable, AuthError, BadRequest,
)
from .telemetry import snapshot, flush, reset
```

- `GatekeptLLM(model: str, base_url: str | None, api_key: str)` — drop-in for `crewai.LLM`.
- `http_post(url, headers, json, *, provider) -> dict` — for non-LLM API calls.
- `snapshot() -> dict[provider, Counters]` — current call/token totals.
- `flush() -> None` — print snapshot to stdout, reset counters.
- `reset() -> None` — clear counters (used by tests).
- The five exception classes are the only error shapes consumers may catch.

These are what later components (`market_book`, future evaluators) depend on.
Internals (`rate_limiter`, `retry`, the per-file split) are not part of the contract.

## File layout (each ≤ 150 code lines, §3.2)

- `src/reasearch_crew/gateway/__init__.py` — public re-exports (~10 lines).
- `src/reasearch_crew/gateway/errors.py` — five-class exception hierarchy + a
  `from_provider_exception(exc) -> GatewayError` translator (~50 lines).
- `src/reasearch_crew/gateway/rate_limiter.py` — token-bucket per provider, loads
  config on first use, `acquire(provider)` blocks if needed (~90 lines).
- `src/reasearch_crew/gateway/retry.py` — `tenacity`-built retry policy factory; one
  policy per provider, configurable from `rate_limits.json` (~50 lines).
- `src/reasearch_crew/gateway/telemetry.py` — `Counters` dataclass, module-level
  registry, `snapshot/flush/reset` (~80 lines).
- `src/reasearch_crew/gateway/llm.py` — `GatekeptLLM(crewai.LLM)`, overrides `.call`
  and `.completion`; wires rate_limiter → retry → telemetry → error translation
  (~120 lines — the densest file, under the limit).
- `src/reasearch_crew/gateway/http.py` — `http_post` helper with the same wrap stack
  for non-LLM endpoints (~80 lines).
- `src/reasearch_crew/config/rate_limits.json` — extend the existing stub with real
  per-provider entries (`openrouter`, `anthropic`, `serper`) and the retry knobs.

Test layout (each ≤ 150 lines):

- `tests/unit/test_gateway_errors.py` — translation table + class hierarchy.
- `tests/unit/test_gateway_rate_limiter.py` — token bucket math + sleep behaviour.
- `tests/unit/test_gateway_retry.py` — 429/5xx triggers retry, 401 does not.
- `tests/unit/test_gateway_telemetry.py` — counters increment, snapshot/reset.
- `tests/unit/test_gateway_http.py` — `http_post` with httpx mock.
- `tests/unit/test_gateway_llm.py` — `GatekeptLLM` integrates rate/retry/telemetry.
- `tests/integration/test_gateway_in_crew.py` — kickoff routes through gatekeeper.

## ADRs (decision · rationale · alternative)

- **ADR-G1 — Subclass `crewai.LLM`; don't monkey-patch `litellm`.**
  · Rationale: explicit subclass survives litellm version bumps and is debuggable in a
  stack trace. Monkey-patching ties us to a specific litellm internal API.
  · Rejected: `monkeypatch_litellm.completion = wrapped` — too implicit.

- **ADR-G2 — Single shared module-level singleton for limiter / telemetry.**
  · Rationale: CrewAI runs one process per kickoff; sharing state across all
  `GatekeptLLM` instances lets one rate limit cover both `researcher` and
  `competitor_analyst` agents pointed at the same provider.
  · Rejected: per-instance state — would let two agents double the effective rate.

- **ADR-G3 — `tenacity` for the retry policy.**
  · Rationale: declarative, jitter built-in, already transitively present.
  · Rejected: hand-rolled `for attempt in range(N)` — would reinvent jitter and
  exception-type matching badly.

- **ADR-G4 — Stable domain exception hierarchy isolates consumers from litellm.**
  · Rationale: the bootstrap already got bit once by a litellm.NotFoundError pattern
  bleed; agents should `except RateLimitExceeded:` and not care what provider raised.
  · Rejected: re-export litellm exceptions — leaks the dependency.

- **ADR-G5 — Token-bucket > leaky-bucket.**
  · Rationale: bursts are normal (researcher fires 5 quick calls before sleeping during
  long writer task). Token-bucket allows burst-then-throttle; leaky-bucket would
  introduce artificial latency on burst boundaries.

## Concurrency / gatekeeper / config notes

- **Concurrency:** CrewAI `Process.sequential` ⇒ single in-flight call. The limiter
  still acquires per call (so the second call waits if the first ate the burst budget).
  When the future hierarchical process lands, the singleton already handles it.
- **Gatekeeper (§5.1):** *this component is the gatekeeper.* Once it lands, `crew.py`'s
  `_get_llm` returns `GatekeptLLM`, not raw `crewai.LLM`. The CLAUDE.md "frozen
  invariants" line gets a new entry: "all external API calls go through
  `src/reasearch_crew/gateway/`; importing `litellm`, `anthropic`, or making raw
  `httpx`/`requests` calls outside `gateway/` is a Segal §5.1 violation."
- **Config (§7.2):** `rate_limits.json` schema (v 1.00):
  ```json
  {
    "version": "1.00",
    "retry": { "max_attempts": 3, "base_delay_sec": 1.0, "jitter": "full" },
    "providers": {
      "openrouter": { "rpm": 20, "tpm": null, "burst": 5 },
      "anthropic":  { "rpm": 50, "tpm": 40000, "burst": 10 },
      "serper":     { "rpm": 60, "tpm": null, "burst": 5 }
    }
  }
  ```
  No rate-limit number lives in `.py`. The provider name is the only key agents pass.
