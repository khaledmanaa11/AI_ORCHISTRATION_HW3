# PRD — market_book

> Triplet: this · [PLAN](PLAN_market_book.md) · [TODO](TODO_market_book.md)

| Field | Value |
|---|---|
| Component | market_book |
| Version | 1.00 |
| Depends on | bootstrap (B1–B9 green) · api_gatekeeper (G1–G10 green) |

## 1. Description & theoretical background (§2.3)

**market_book** is the actual product: a CrewAI pipeline that researches a real market
and emits a small, polished **Hebrew PDF book**. The subject of v1.00 is a market
research report on **ALYASMEEN** — a WhatsApp commerce agent for small businesses
(conversational ordering + a business dashboard for orders, sales, products, and
broadcasts).

The pipeline is three logical roles, mapped to Segal's "orchestration IS the method":

1. **Researcher** — gathers *grounded* market facts. Grounding is non-negotiable
   (CLAUDE.md: "never invents facts"), so the researcher uses a **search tool that
   routes through the existing gateway** (`gateway.http_post`, provider `serper` —
   already present in `rate_limits.json`). Output: a research brief + a small set of
   **sourced numbers** (market sizing, adoption rates, conversion figures) with their
   citations.
2. **Author** — turns the brief into the book *content* as Hebrew **Markdown**:
   abstract, sections, **≥1 table**, **≥1 figure**, **≥1 graph** (as data, not pixels),
   and an **equations** section (unit economics / market sizing) with short derivations.
3. **Typesetter** — an agent whose **deterministic tool** renders the Hebrew Markdown to
   **XeLaTeX** (via `pandoc` + a fixed Hebrew template) and compiles it to **PDF** (via
   `xelatex`). The LLM orchestrates; the *mechanical* conversion is deterministic.

Theoretically this is a *grounded-generation pipeline* (retrieval → composition →
deterministic typesetting). The reliability seam is the same lesson the gatekeeper
taught: keep the fragile, non-deterministic work (LLM authoring) separate from the work
that must be byte-exact (LaTeX that actually compiles in right-to-left Hebrew).

## 2. Inputs / Outputs / performance metrics (§2.3)

- **Input:** `config/book.json` (topic, title, author, language=`he`, Hebrew font,
  page target, output paths) + `GEMINI_API_KEY` (LLM) + optional `SERPER_API_KEY`
  (grounding). All knobs from config/env (§7.2) — zero hardcoded values.
- **Intermediate outputs:** `output/research.md` (brief), `output/data.json` (typed,
  sourced figures), `output/book.he.md` (Hebrew Markdown), `output/book.he.tex`.
- **Final output:** `output/book.pdf` — a Hebrew PDF book, **at least 30 pages**,
  containing at minimum: one table, one figure (image asset), one graph, one proved
  equation block. The 30-page floor drives content volume: the Author composes the book
  **section-by-section** (see ADR-D6) so no single LLM response is truncated.
- **Performance / quality metrics:**
  - PDF compiles with **0 XeLaTeX errors**; Hebrew renders right-to-left.
  - Every numeric claim in `data.json` carries a source string (grounded).
  - Token cost reported via `gateway.flush()` after kickoff (§11). Dollar cost = $0
    (Gemini + Serper free tiers).

## 3. Functional requirements

- **FR-D1** — The LLM provider is **config-driven and free**: `config/llm.json` selects
  Gemini (`gemini/gemini-2.0-flash`, `api_key_env: GEMINI_API_KEY`); `rate_limits.json`
  gains a `gemini` provider block. No model id or limit hardcoded in `.py`. (Resolves the
  B10/G11 model-thrash; provider swap is config-only thanks to the gateway.)
- **FR-D2** — A **search tool** `tools/search.py::web_search(query)` performs grounding
  queries **exclusively through `gateway.http_post(..., provider="serper")`** (§5.1). No
  raw `httpx`/`requests` in the tool. Missing `SERPER_API_KEY` degrades gracefully: the
  researcher proceeds LLM-only and the book renders an "unverified data" banner.
- **FR-D3** — The **Researcher** agent uses `web_search` and emits `output/research.md`
  plus a fenced, machine-readable block of sourced figures. A deterministic loader
  validates that block into `output/data.json` (typed; every figure has `value`,
  `unit`, `source`).
- **FR-D4** — The **Author** agent emits `output/book.he.md`: a Hebrew book with an
  abstract, ≥3 sections, **≥1 booktabs table**, **≥1 figure reference**, **≥1 graph**
  (declared as data, rendered later by pgfplots), and an **equations section**.
- **FR-D5** — An **economics module** `report/economics.py` computes the report's core
  equations from `data.json` (e.g. market sizing `TAM ⊇ SAM ⊇ SOM`, unit economics
  `LTV`, `CAC`, payback period) and returns both the **LaTeX form** and the **numeric
  result**, so each equation is *proved against real numbers*, not decorative.
- **FR-D6** — A **figures module** `report/figures.py` emits, from `data.json`: a
  `pgfplots` graph snippet and a `booktabs` table snippet (Hebrew-aware). At least one
  raster **image asset** (`assets/`) is embedded via `\includegraphics`.
- **FR-D7** — A **Hebrew XeLaTeX template** `templates/book.he.tex` sets up
  `polyglossia` (main language Hebrew) + `bidi`, a configurable Hebrew font,
  `booktabs`, `pgfplots`, `graphicx`. Content is injected by pandoc; the template holds
  **no report text**.
- **FR-D8** — A **render tool** `report/render.py::markdown_to_latex` runs `pandoc`
  (deterministic) with the Hebrew template to produce `book.he.tex`; a **compile tool**
  `report/compile.py::compile_pdf` runs `xelatex` (engine + flags from config) to
  produce `book.pdf`. Both are subprocess wrappers — **local processes, not external
  APIs**, so they do not pass through the gateway, but they raise typed errors on
  failure.
- **FR-D9** — The **Typesetter** agent owns render+compile as a tool. `crew.py` wires
  the three agents `Process.sequential` (research → author → typeset). `main.py` feeds
  inputs from `book.json` and calls `gateway.flush()` after kickoff.

## 4. Constraints, limitations, alternatives considered (§2.3)

- **Gemini free tier over OpenRouter free slugs.**
  · Rationale: OpenRouter free model ids kept disappearing (the B10 thrash:
  `deepseek-v4-pro`, a *reranker* slug, `gemma-4-31b-it`). Google AI Studio gives a
  stable free key and is materially stronger at **Hebrew** — and Hebrew is the whole
  deliverable. Cost stays $0.
  · Rejected: staying on OpenRouter `:free` — unreliable availability, weaker Hebrew.
- **Deterministic pandoc + XeLaTeX for typesetting; the LLM never writes raw LaTeX.**
  · Rationale: an LLM cannot reliably emit byte-exact RTL Hebrew XeLaTeX that compiles;
  one stray brace fails the build. A fixed template + pandoc is reproducible.
  · Rejected: "ask the Author to output `.tex`" — fragile, unverifiable, RTL-fragile.
- **Graph as `pgfplots` data, not a generated PNG.**
  · Rationale: text-defined, compiles in-engine, no extra image binary, diffable, uses
  the *real* numbers from `data.json`.
  · Rejected: matplotlib→PNG — adds a runtime image step and a binary artifact for no
  quality gain at book scale. (One real raster asset is still embedded to satisfy the
  "image" requirement.)
- **Serper.dev free tier for grounding.**
  · Rationale: 2,500 free queries, no recurring cost, already wired in the gateway.
  · Rejected: paid search APIs (violates "pay nothing"); LLM-only (ungrounded — only a
  graceful fallback, never the default).

## 5. Success criteria & test scenarios (§2.3)

- **R-AC1** — With a mocked LLM + mocked `pandoc`/`xelatex`, a full kickoff produces the
  artifact chain ending in a `book.pdf` path. → integration test asserts each stage's
  output file path is produced in order.
- **R-AC2** — `web_search` routes through `gateway.http_post` with `provider="serper"`;
  a missing key yields the documented LLM-only fallback (no crash). → unit test mocks
  `http_post`; second test unsets the key and asserts the fallback banner flag.
- **R-AC3** — The figures `data.json` → `pgfplots`/`booktabs` snippets are well-formed
  and contain the real values. → unit test asserts table rows and plot coordinates match
  `data.json`.
- **R-AC4** — `economics.py` returns the correct numeric result *and* a LaTeX string for
  each equation, computed from `data.json` (e.g. `LTV = ARPU × margin × lifetime`). →
  unit test asserts the number against a hand-computed fixture.
- **R-AC5** — The Hebrew template + a tiny Markdown fixture compile to a non-empty PDF in
  CI-skippable form: the *render* call passes the template path and `--pdf-engine=xelatex`
  to pandoc. → unit test asserts the exact argv (subprocess mocked); a `@pytest.mark`
  guards the real-binary path so the gate stays green without TeX installed.

## Non-goals

- **A live ALYASMEEN dashboard / WhatsApp integration** — out of scope; this component
  *researches* that business, it does not build it.
- **Multi-language output** — Hebrew only in v1.00; an English edition is a later triplet.
- **Automatic image sourcing from the web** — one curated asset is bundled; scraping
  licensed imagery is out of scope.
- **A LaTeX-authoring LLM** — explicitly rejected (see §4); typesetting stays
  deterministic.
- **Streaming / hierarchical crew** — sequential process only, consistent with the
  gatekeeper's v1.00 assumptions.
