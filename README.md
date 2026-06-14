# reasearch_crew — grounded research → Hebrew PDF book

> Orchestration AI · HW3. A [CrewAI](https://crewai.com) multi-agent pipeline that
> researches a market (ALYASMEEN), grounds the findings in real sourced figures, and
> typesets a ≥30-page Hebrew PDF book — every external API call funneled through a single
> gatekeeper seam.

**Status: ✅ complete.** The pipeline ran end-to-end on real keys and delivered
`output/book.pdf` — **41 pages** of grounded Hebrew market research with an AI-generated
cover, a real TAM→SAM→SOM funnel ($45B → $9.86B → $296M) and live unit economics
(LTV $1,481.25 · CAC $588.24 · payback 9.93 mo). See `docs/PROGRESS.md` for the full log.

## What it does

Three agents run `Process.sequential`:

1. **Researcher** — web-searches for ALYASMEEN market figures (`tools/search.py` → Serper),
   parses them into a validated `output/data.json` dataset.
2. **Author** — writes the book section-by-section in Hebrew (`output/book.he.md`),
   driven over an outline so each section clears a per-section length floor and the whole
   clears 30 pages despite the model's output-token ceiling.
3. **Typesetter** — runs market-sizing/unit-economics equations and pgfplots figures,
   renders Markdown → LaTeX (pandoc) and LaTeX → PDF (XeLaTeX + polyglossia + bidi),
   producing `output/book.pdf` with an AI-generated cover.

## Architecture

```
reasearch_crew/src/reasearch_crew/
├── crew.py            # agent/task wiring, GatekeptLLM
├── main.py            # entry point; inputs from book.json; flush() token totals
├── settings.py        # config loaders
├── config/            # agents.yaml, tasks.yaml, book.json, rate_limits.json,
│                      #   endpoints.json, llm.json   (no hardcoded host/model/key)
├── gateway/           # the ONLY egress seam for external API calls
│   ├── llm.py         #   GatekeptLLM(crewai.LLM) — forces the litellm path
│   ├── credentials.py #   config-driven phase credential resolution
│   ├── http.py        #   http_post: limiter + retry + telemetry + translate
│   ├── rate_limiter.py#   per-provider token bucket
│   ├── retry.py       #   tenacity: 3 retries on 429/5xx, none on 401/400
│   ├── telemetry.py   #   counters + snapshot / flush / reset
│   └── errors.py      #   five-class typed exception hierarchy
├── report/            # dataset, economics, figures, render, compile, assemble, cover
├── tools/             # search.py (Serper), typeset.py (pandoc/xelatex)
└── templates/         # book.he.tex (XeLaTeX, configurable Hebrew font)
```

**Frozen invariant:** all external API calls go through `gateway/`. Importing `litellm`,
`anthropic`, or making raw `httpx`/`requests` calls outside `gateway/` is a violation. The
typed exceptions in `gateway/errors.py` are the only error shape consumers may catch.
(`pandoc`/`xelatex` are local subprocesses, explicitly out of the gateway's network scope,
but still raise a typed `report.errors.TypesetError`.)

## Setup

Requires Python `>=3.10,<3.14` and [uv](https://docs.astral.sh/uv/). Everything runs through
`uv` — no `pip` / `python -m` / `venv`.

```bash
cd reasearch_crew
uv sync --frozen
```

Copy `.env-example` to `.env` in the repo root and fill in your keys:

```
GEMINI_API_KEY_RESEARCH=  # Researcher agent
GEMINI_API_KEY_COMPOSE=   # section-by-section composition
GEMINI_API_KEY_TYPESET=   # Typesetter agent and cover generation
SERPER_API_KEY=           # optional serper.dev grounded web search
```

Use a separate Google AI Studio project/key for each Gemini phase. The pipeline does not
fall back to a shared key when a required phase key is missing. The model is
`gemini/gemini-2.5-flash` (Gemini free tier); the constraint is rate limits, not cost
(free tier is ~5 RPM; dollar cost ≈ $0).

### Typesetting prerequisites (for the live PDF run)

Resolved from `config/book.json.bin` (never PATH): **pandoc**, **xelatex** (MiKTeX / TeX Live),
and a Hebrew font (`book.json.hebrew_font`, default **David**). Tests mock these subprocesses;
only the live run needs them installed.

## Running

```bash
cd reasearch_crew
uv run run_crew
```

This kicks off the crew and produces `output/book.pdf` (≥30 pp, Hebrew, with the generated
cover) and prints the gateway `flush()` telemetry — per-provider call counts, retries and
cost. On the delivered run that was 27 Gemini text calls + 1 image + 12 Serper searches, at
**$0.00** (free tier is rate-capped, not cost-capped). Per-token in/out read 0 because
crewai's litellm path hands `.call` only the completion text, with no `usage` block to count —
a documented telemetry limitation; the dollar cost is $0 regardless.

## Tests & the gate

```bash
uv run ruff check src tests   # 0 errors
uv run pytest -q              # 0 failures (TDD)
uv run pytest --cov           # ≥ 85% coverage
```

Tests always mock the LLM client — no test touches the live API.

## Project conventions

This project follows the Segal V3 guidelines (`docs/SEGAL_GUIDELINES_V3.md`) and a
Director/Orchestrator/Developer relay workflow. See `CLAUDE.md` for the enforced essentials
and `docs/PROGRESS.md` for the single source of truth on status.
