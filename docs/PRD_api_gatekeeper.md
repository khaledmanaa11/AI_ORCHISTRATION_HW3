# PRD — api_gatekeeper

> Triplet: this · [PLAN](PLAN_api_gatekeeper.md) · [TODO](TODO_api_gatekeeper.md)

| Field | Value |
|---|---|
| Component | api_gatekeeper |
| Version | 1.00 |
| Depends on | bootstrap (B1–B9 already green) |

## 1. Description & theoretical background (§2.3)

The **API Gatekeeper** is the single seam through which every external API request
leaves this process. Segal §5.1 mandates that no agent, tool, or pipeline stage may
talk to an external provider directly — every LLM completion (OpenRouter, Anthropic),
every search call (Serper), every other HTTP call to a third party has to go through
the gatekeeper.

Theoretically, this is a *facade + interceptor* pattern over CrewAI's `LLM` class and
the `requests`/`httpx` stack. The facade hides provider-specific exception types behind
a stable domain hierarchy (`GatewayError` and subclasses). The interceptor layer adds
three cross-cutting concerns the agents would otherwise duplicate: **rate limiting**
(token bucket per provider, values from `config/rate_limits.json` per §5.2), **retries
with exponential backoff** (transient 429s and 5xx), and **telemetry** (in-memory token
+ call counters that survive across a kickoff so we can later attribute cost per agent).

The bootstrap proved why this seam matters: when OpenRouter killed the `:free` slug
between morning and afternoon on 2026-06-10, the swap was one config line because the
LLM was already construction-isolated. The gatekeeper extends that isolation to *call
behavior*, not just *configuration*.

## 2. Inputs / Outputs / performance metrics (§2.3)

- **Input (LLM path):** a `messages: list[dict]` sequence + the provider name resolved
  from the calling agent's LLM config (`openrouter` or `anthropic`).
- **Input (HTTP path):** `(url: str, headers: dict, json: dict, provider: str)` — used
  by Serper and any future non-LLM API tool.
- **Output (success):** raw provider response object pass-through for LLM (CrewAI
  needs the litellm shape); parsed JSON dict for HTTP.
- **Output (failure):** an instance of the gateway exception hierarchy
  (`RateLimitExceeded`, `ProviderUnavailable`, `AuthError`, `GatewayError`) — never a
  raw `litellm.NotFoundError` / `httpx.HTTPStatusError` leaking to the caller.
- **Performance:** added latency ≤ 10 ms p99 on the happy path (no retries). Retry
  policy: 3 attempts, exponential backoff 1s/2s/4s with full jitter. Rate limiter
  must never spin-block — sleeps with a single timer per acquisition.

## 3. Functional requirements

- **FR-G1** — `crewai.LLM` is subclassed by `GatekeptLLM` such that every
  `Agent.execute_task` LLM call is intercepted by the gatekeeper. Crew.py constructs
  `GatekeptLLM` instances instead of raw `LLM` instances; the substitution is
  invisible to the rest of CrewAI (same public API).
- **FR-G2** — Per-provider rate limits are read from `config/rate_limits.json`
  (already stubbed at "version": "1.00"). Schema:
  `{providers: {<name>: {rpm: int, tpm: int|null, burst: int}}}`. No rate-limit
  number is hardcoded in `.py`.
- **FR-G3** — Transient failures (HTTP 429, 5xx, `ConnectionError`, `TimeoutError`)
  retry with exponential backoff via `tenacity`. Max attempts and base delay are read
  from `rate_limits.json`. The 4th 429 raises `RateLimitExceeded`.
- **FR-G4** — Provider-specific exceptions are translated to a stable domain hierarchy:
  - `GatewayError` (base)
  - `RateLimitExceeded(GatewayError)` — for 429 after retries are exhausted
  - `ProviderUnavailable(GatewayError)` — for 5xx after retries exhausted
  - `AuthError(GatewayError)` — for 401/403 (no retry; misconfigured key)
  - `BadRequest(GatewayError)` — for 400/404 (no retry; bug in our request)
- **FR-G5** — A `Telemetry` collector tracks per-provider: call count, retry count,
  input tokens, output tokens. The current kickoff's totals are queryable via
  `gateway.telemetry.snapshot()`. The numbers print on `gateway.flush()` (called from
  `main.py` after kickoff).
- **FR-G6** — A `gateway.http_post(url, headers, json, *, provider)` helper exists
  for non-LLM API calls (Serper.dev, future tools). Same rate-limit + retry +
  exception-translation semantics as the LLM path.

## 4. Constraints, limitations, alternatives considered (§2.3)

- **Subclass `crewai.LLM` rather than monkey-patch `litellm`.**
  · Rationale: explicit, debuggable, survives litellm version bumps without breaking.
  · Rejected: monkey-patching `litellm.completion` — opaque, fragile, and would also
  affect non-CrewAI code paths if any ever land.
- **`tenacity` for retry policy.**
  · Rationale: battle-tested, declarative, already a transitive dep of crewai.
  · Rejected: hand-rolled `while attempt < N` — error-prone, no jitter primitives.
- **Process-local token-bucket rate limiter.**
  · Rationale: this is a single-process CrewAI app (sync, sequential). A distributed
  limiter (Redis, etc.) is YAGNI until we run more than one process.
  · Rejected: Redis-backed limiter (operational overhead with no current benefit).
- **No caching layer in v1.00.**
  · Rationale: caching LLM responses changes semantics (mocks differ from prod) and is
  separate from the gatekeeper's safety responsibilities.
  · Rejected: built-in cache — out of scope; a future triplet if a use case emerges.

## 5. Success criteria & test scenarios (§2.3)

- **R-AC1** — A `ReasearchCrew().crew().kickoff(...)` (with mocked litellm) routes
  every `LLM.call` through `GatekeptLLM.call`. → test: integration spy fixture asserts
  intercept count ≥ 1.
- **R-AC2** — Simulated 429 from the underlying provider triggers exactly 3 retries
  with exponential delays (1s/2s/4s); the 4th raises `RateLimitExceeded`. → test:
  unit test mocks litellm to raise rate-limit error N times, asserts retry behavior.
- **R-AC3** — Editing `config/rate_limits.json` to set `openrouter.rpm = 1` and
  making 2 calls within 1 sec causes the second call to sleep ≈ 1 sec. → test:
  unit test with monkeypatched `time.sleep` records the sleep duration.
- **R-AC4** — `gateway.http_post` against a provider configured at 1 RPS waits ≈ 1 sec
  between consecutive calls. Provider errors translate to `GatewayError` subclasses.
  → test: unit test with httpx mock + monkeypatched sleep.
- **R-AC5** — `gateway.telemetry.snapshot()` reports correct call/token counts after
  a mocked kickoff with 5 calls (3 OpenRouter + 2 Anthropic). → test: unit test asserts
  per-provider counts.

## Non-goals

- **Caching of LLM responses** — separate concern; would change kickoff semantics.
- **Distributed rate limiting** — single-process is enough until proven otherwise.
- **Streaming responses** — CrewAI sequential process uses sync non-streaming calls;
  gatekeeper assumes non-streaming. Streaming support is a future triplet.
- **Cost attribution per agent** — telemetry is per-provider in v1.00; per-agent split
  needs CrewAI hooks the bootstrap didn't expose, defer to a later triplet.
- **A general circuit breaker** — retries cover transient flakes; if a provider is
  fully down, the user sees `ProviderUnavailable` and re-runs later. No fancy half-open
  state machine.
