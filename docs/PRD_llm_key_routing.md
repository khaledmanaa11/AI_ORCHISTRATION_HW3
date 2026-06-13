# PRD - llm_key_routing

> Triplet: this - [PLAN](PLAN_llm_key_routing.md) - [TODO](TODO_llm_key_routing.md)

| Field | Value |
|---|---|
| Component | llm_key_routing |
| Version | 1.00 |
| Depends on | market_book D1, D16, D17 |

## 1. Problem

The live market-book pipeline currently depends on one Gemini API key. Research,
section-by-section composition, typesetting orchestration, and cover generation can
therefore exhaust one free-tier project quota before `output/book.pdf` is complete.

The pipeline must use three separately configured Gemini keys:

- `GEMINI_API_KEY_RESEARCH` for the Researcher agent.
- `GEMINI_API_KEY_COMPOSE` for all section composition calls.
- `GEMINI_API_KEY_TYPESET` for the Typesetter agent and Gemini cover generation.

## 2. Requirements

- **FR-K1** - Key environment-variable names are declared in `config/llm.json`; Python
  source contains no Gemini key-env literals.
- **FR-K2** - Each phase resolves only its assigned key and raises a clear error naming
  the missing environment variable before making an LLM call.
- **FR-K3** - `GatekeptLLM` remains the only LLM path. Each phase has a separately cached
  `GatekeptLLM`, and every completion still passes through the gateway.
- **FR-K4** - Cover generation uses the typeset key through shared credential-resolution
  code and continues to fall back to the bundled image when that key is unavailable.
- **FR-K5** - Tests isolate all Gemini environment variables from the developer's real
  `.env`; no test may accidentally read or print a live credential.
- **FR-K6** - `.env-example`, README, standing instructions, and D15 live-run directions
  document the three-key contract instead of the retired shared-key contract.
- **FR-K7** - The current configured Gemini model is not changed by this feature.

## 3. Acceptance criteria

- **K-AC1** - A unit test supplies three distinct fake values and proves the Researcher,
  composer, and Typesetter each receive the correct value and distinct cached LLM.
- **K-AC2** - Missing any required phase key raises an error that names that phase's env
  variable; no fallback silently moves LLM traffic onto another phase's quota.
- **K-AC3** - Cover tests prove the typeset key is sent only through `gateway.http_post`;
  missing typeset key returns the bundled fallback without a network call.
- **K-AC4** - The full mocked pipeline produces all artifacts while the three phase keys
  are configured and telemetry still reports Gemini calls.
- **K-AC5** - `rg "GEMINI_API_KEY"` in Python source finds no hardcoded env-var name.
- **K-AC6** - Ruff, pytest, coverage, file-size, security, and gateway-invariant gates pass.

## 4. Non-goals

- Rotating keys automatically after a quota error.
- Running phases concurrently.
- Changing Gemini models, provider limits, retry policy, Serper credentials, or TeX tools.
- Performing a live API call in tests.
