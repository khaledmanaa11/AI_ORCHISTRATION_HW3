# PROGRESS — single source of truth

NEXT: ✅ DONE — all parts (B, C, D) complete; the live book is delivered. Submission-ready.

> STATUS: project complete. The ALYASMEEN pipeline ran end-to-end on real keys and
> produced `output/book.pdf` — 41 pages of grounded Hebrew market research with an
> AI-generated cover, a real TAM→SAM→SOM funnel ($45B→$9.86B→$296M) and live unit
> economics (LTV $1,481.25 · CAC $588.24 · payback 9.93 mo). Every external call went
> through the gateway. See the §11 token-cost note under D15.
>
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
- [x] B10 — [HUMAN] Live run. SUPERSEDED by D1 (switched to Gemini free tier; OpenRouter slugs kept disappearing) and closed by the real live run, D15.

## Part C — api_gatekeeper (single egress seam for all external API calls — §5.1)
Triplet: [PRD](PRD_api_gatekeeper.md) · [PLAN](PLAN_api_gatekeeper.md) · [TODO](TODO_api_gatekeeper.md) — TBDs locked 2026-06-10 with documented defaults; Director redlines before G1.

- [x] G1 — Add `gateway/errors.py` + `gateway/__init__.py`: five-class exception hierarchy + provider→domain translator.
- [x] G2 — Populate `config/rate_limits.json` with v1.00 schema (retry block + 3 providers); `uv add tenacity`.
- [x] G3 — Add `gateway/rate_limiter.py`: token-bucket per provider, sleeps when burst exhausted.
- [x] G4 — Add `gateway/retry.py`: tenacity policy, 3 retries on 429/5xx, no retry on 401/400.
- [x] G5 — Add `gateway/telemetry.py`: Counters + snapshot / flush / reset.
- [x] G6 — Add `gateway/http.py`: `http_post` wraps httpx with the same limiter/retry/telemetry/translate stack.
- [x] G7 — Add `gateway/llm.py`: `GatekeptLLM(crewai.LLM)` overrides `.call` / `.completion`; `crew.py::_get_llm` returns `GatekeptLLM`.
- [x] G8 — Update existing bootstrap tests for the subclass; add `gateway/` to coverage scope.
- [x] G9 — Integration test: kickoff routes through gatekeeper (R-AC1).
- [x] G10 — Update CLAUDE.md frozen invariant: no `litellm` / `anthropic` / raw `httpx` imports outside `gateway/`.
- [x] G11 — [HUMAN] Live `uv run run_crew` with gateway. SUPERSEDED by D15 and closed there: the live run produced the actual Hebrew PDF, every call routed through the gateway, and `flush()` reported the telemetry totals.

## Part D — market_book (the product: grounded research → Hebrew PDF book on ALYASMEEN)
Triplet: [PRD](PRD_market_book.md) · [PLAN](PLAN_market_book.md) · [TODO](TODO_market_book.md) — approved 2026-06-11; keys (GEMINI + SERPER) in `.env`, xelatex/pandoc/David font verified present.

- [x] D1 — Switch LLM to Gemini free (`gemini/gemini-2.0-flash`, `GEMINI_API_KEY`); add `gemini` to `rate_limits.json`; update `.env-example` + B8 model assertions. (Closes B10/G11 model-thrash.)
- [x] D2 — Add `config/book.json` (v1.00 schema: topic/title/he/font=David/page_target=30/bin/paths) + `assets/` with one curated image. (`settings.py` loader; `assets/alyasmeen.png`.)
- [x] D3 — `tools/search.py::web_search` via `gateway.http_post(provider="serper")`; missing-key fallback. (Serper URL in `config/endpoints.json`.)
- [x] D4 — `report/dataset.py`: parse Researcher's sourced figures → validated `output/data.json`.
- [x] D5 — Rewrite `agents.yaml`/`tasks.yaml` for the ALYASMEEN Researcher; wire `web_search` in `crew.py`.
- [x] D6 — `report/economics.py`: market-sizing + unit-economics equations, each `.latex` + `.value` from `Dataset`.
- [x] D7 — `report/figures.py`: pgfplots graph + booktabs table from `Dataset`.
- [x] D8 — Author agent + writing task → `output/book.he.md`, section-by-section to ≥30 pages (Hebrew). (`report/outline.py`.)
- [x] D9 — `templates/book.he.tex`: XeLaTeX + polyglossia + bidi + configurable font; no report text.
- [x] D10 — `report/render.py::markdown_to_latex` (pandoc via `book.json.bin.pandoc`); typed `TypesetError`.
- [x] D11 — `report/compile.py::compile_pdf` (xelatex via `book.json.bin.xelatex`); typed `TypesetError`.
- [x] D12 — `tools/typeset.py` + Typesetter agent; wire 3 agents `Process.sequential` in `crew.py`. (`report/assemble.py`.)
- [x] D13 — `main.py` inputs from `book.json` + `gateway.flush()`; integration test for the full artifact chain.
- [x] D14 — Gate hygiene: coverage scope for `report/`+`tools/`, ≥85% (99%), ≤150 LOC/file; docs update.
- [x] D16 — Deliver the section-by-section Author that D8/TBD-D6 promised but never shipped:
  the live book is 14 pp, not 30, because `writing_task` is a SINGLE LLM call capped by
  Gemini's output-token ceiling. Drive the Author one section at a time over
  `section_outline()`, append each to `output/book.he.md`, and inject a per-section length
  floor (from `book.json`) so each section is substantial. Every call stays gatekept.
- [x] D17 — Replace the static placeholder image with a real AI-generated ALYASMEEN cover
  via a gatekept image API (overrides TBD-D5). New `gateway/` image client through the same
  limiter/retry/telemetry/translate stack; prompt derived from `book.json`; missing key
  falls back to the bundled raster. No image API call outside `gateway/`.
- [x] D18 — Route the pipeline through three required, config-driven Gemini keys:
  Researcher (`GEMINI_API_KEY_RESEARCH`), section composer (`GEMINI_API_KEY_COMPOSE`),
  and Typesetter plus cover generation (`GEMINI_API_KEY_TYPESET`). Centralize credential
  resolution beside the gateway, isolate tests from real `.env` values, and update setup
  documentation. Triplet approved 2026-06-13.
- [x] D15 — [HUMAN] Live `uv run run_crew` with real keys + TeX. Live research (flash) produced
  8 real, sourced, non-zero figures + a 20.9k-word section-by-section compose; the run exposed
  two parser/typeset gaps (an unclosed ```json fence; verbatim overflow from fenced/indented
  prose) fixed in 502a79c / ab29ee2. `output/book.pdf` rebuilt offline from the live data —
  **41 pages**, AI cover, real TAM→SAM→SOM ($45B→$9.86B→$296M), LTV $1,481.25 / CAC $588.24 /
  payback 9.93 mo. Goal met (≥30 pp, grounded, gatekept).

### §11 token-cost analysis (from the live run's `flush()`)
| provider | API calls | retries | dollar cost |
|---|---|---|---|
| gemini (text) | 27 | 1 | $0.00 |
| gemini (image, cover) | 1 | 0 | $0.00 |
| serper (web search) | 12 | 0 | $0.00 |

Total cost **$0.00** — Gemini free tier is rate-capped, not cost-capped (the real constraint,
per design). Per-token in/out came back 0: crewai's litellm path returns only the completion
text to `GatekeptLLM.call`, so the response carries no `usage` block for the gateway to count.
A documented telemetry limitation, not a cost item — dollar cost is $0 regardless of token volume.

### Blocked steps
_(none — project complete)_
