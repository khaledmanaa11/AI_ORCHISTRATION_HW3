# TODO — market_book

> Triplet: [PRD](PRD_market_book.md) · [PLAN](PLAN_market_book.md) · this
> Atomic steps in build order — each maps to PRD IDs. **One step = one commit = one /relay-next.**
> Every step has a Definition of Done (§2.2). When approved, copy these into `docs/PROGRESS.md`.

## Build order

- [x] **D1** — Switch the LLM to Gemini free tier (also closes the B10/G11 model-thrash).
  Edit `config/llm.json` → `model: "gemini/gemini-2.0-flash"`, `api_key_env:
  "GEMINI_API_KEY"`. Add `"gemini": { "rpm": 15, "tpm": 1000000, "burst": 5 }` to
  `rate_limits.json`. Add `GEMINI_API_KEY=` to `.env-example`. Update the B8 model
  assertion. (Satisfies FR-D1; **DoD:** `uv run pytest -q` green; the gateway resolves
  provider `gemini` from the model prefix in a unit test; no model id in any `.py`.)
  > **Audit 2026-06-11 — D1 is partially applied and currently RED.** `llm.json` is already
  > on `gemini/gemini-2.0-flash`, but the suite fails (16 failed / 56 passed): `GatekeptLLM`
  > can't construct because the native provider dep is missing, and the OpenRouter-era
  > fixtures/asserts were never updated. D1 is NOT done until these are all true:
  > - [ ] `uv add 'crewai[google-genai]'` — the Gemini native provider; currently absent
  >   from `pyproject.toml:8` (only `crewai[tools]`). Without it: `ImportError: Google Gen
  >   AI native provider not available`.
  > - [ ] `tests/conftest.py:15` `api_key` fixture sets `GEMINI_API_KEY` (not `OPENROUTER_API_KEY`).
  > - [ ] `tests/integration/test_gateway_in_crew.py` telemetry asserts use provider
  >   `"gemini"` (not the stale `"openrouter"`).
  > - [ ] B8 model assertion in `test_crew_construction.py` reads `gemini/gemini-2.0-flash`.

- [x] **D2** — Add `config/book.json` (the v1.00 schema in PLAN §config) and an
  `assets/` dir holding **one** curated raster image (e.g. an ALYASMEEN logo/figure).
  (Satisfies §7.2 config externalization; **DoD:** a unit test loads `book.json` and
  asserts `language == "he"` and all `paths.*` keys exist; the asset file is committed.)

- [x] **D3** — Add `tools/search.py::web_search(query, *, max_results=5)` that calls
  **`gateway.http_post(..., provider="serper")`** and normalizes results to
  `[{title, url, snippet}]`. Missing `SERPER_API_KEY` → return `[]` and set an
  "unverified" flag. (Satisfies FR-D2, R-AC2; **DoD:** `tests/unit/test_search_tool.py`
  mocks `http_post` and asserts the provider arg; a second test unsets the key and
  asserts the empty-result fallback. No raw `httpx`/`requests` in the file.)

- [x] **D4** — Add `report/dataset.py`: parse the Researcher's fenced figures block from
  `research.md`, validate every figure has `value`/`unit`/`source`, write `data.json`;
  expose a typed `read_dataset() -> Dataset`. (Satisfies FR-D3; **DoD:**
  `tests/unit/test_dataset.py` proves a sourced figure parses and a source-less figure
  raises; round-trips through `data.json`.)

- [x] **D5** — Rewrite `config/agents.yaml` + `config/tasks.yaml` for the **Researcher**:
  ALYASMEEN market-research role, must use `web_search`, must emit `research.md` + the
  fenced figures block. Wire the tool onto the agent in `crew.py`. (Satisfies FR-D3;
  **DoD:** unit test builds the researcher with the tool attached (LLM mocked); ruff green.)

- [x] **D6** — Add `report/economics.py`: the report's equation set (market sizing
  `TAM/SAM/SOM`, unit economics `LTV`, `CAC`, payback), each returning `.latex` **and**
  `.value` computed from `Dataset`. (Satisfies FR-D5, R-AC4; **DoD:**
  `tests/unit/test_economics.py` asserts each numeric result against a hand-computed
  fixture and that `.latex` is non-empty.)

- [x] **D7** — Add `report/figures.py`: `graph_snippet(ds)` (pgfplots) and
  `table_snippet(ds)` (booktabs), both built from `Dataset`. (Satisfies FR-D6, R-AC3;
  **DoD:** `tests/unit/test_figures.py` asserts the table rows and plot coordinates equal
  the `data.json` values; snippets are balanced LaTeX environments.)

- [x] **D8** — Add the **Author** agent + writing task: emit `output/book.he.md` — Hebrew
  abstract, the table, a figure reference (`assets/` image), the graph, and the equations
  section, authored **section-by-section** to reach the `book.json.page_target` (≥30
  pages) without truncation (ADR-D6). The section outline is config/task-driven; each
  section is appended to `book.he.md`. `agents.yaml`/`tasks.yaml` instructions in Hebrew.
  (Satisfies FR-D4; **DoD:** unit test builds the author + task (LLM mocked) and asserts
  `output_file` is `book.he.md` and that the outline has enough sections to meet the
  page target; tasks.yaml declares the required structural elements.)

- [x] **D9** — Add `templates/book.he.tex`: XeLaTeX + `polyglossia` (main = Hebrew) +
  `bidi`, configurable Hebrew font, `booktabs`, `pgfplots`, `graphicx`. No report text.
  (Satisfies FR-D7; **DoD:** a unit test asserts the template references the font *token*
  (substituted from `book.json`, not hardcoded) and loads the required packages.)

- [x] **D10** — Add `report/render.py::markdown_to_latex(md, tex, *, template)` (pandoc
  subprocess; pandoc path from `book.json.bin.pandoc`, not PATH) raising `TypesetError`
  on failure. (Satisfies FR-D8, R-AC5; **DoD:** `tests/unit/test_render.py` mocks
  subprocess and asserts argv[0] is the configured pandoc path and argv contains the
  template path and `--pdf-engine=xelatex`; non-zero exit raises `TypesetError`.)

- [x] **D11** — Add `report/compile.py::compile_pdf(tex) -> Path` (xelatex subprocess;
  engine path + flags from `book.json.bin.xelatex`) raising `TypesetError` on failure.
  (Satisfies FR-D8; **DoD:** `tests/unit/test_compile.py` mocks subprocess, asserts the
  configured engine argv and a returned `book.pdf` path; non-zero exit raises
  `TypesetError`.)

- [x] **D12** — Add `tools/typeset.py::render_and_compile` and the **Typesetter** agent +
  task; wire all three agents `Process.sequential` in `crew.py`
  (research → author → typeset). (Satisfies FR-D9; **DoD:** unit test builds the
  typesetter with the tool attached (LLM + subprocess mocked); ruff green.)

- [x] **D13** — Edit `main.py`: load inputs from `book.json`, kickoff, then call
  `gateway.flush()`. Add `tests/integration/test_book_pipeline.py`: full kickoff with
  mocked LLM + mocked pandoc/xelatex produces the artifact chain ending at `book.pdf`.
  (Satisfies R-AC1; **DoD:** integration test asserts `research.md → data.json →
  book.he.md → book.he.tex → book.pdf` all produced in order; `flush()` prints token
  totals.)

- [x] **D14** — Gate hygiene + docs: add `report/`, `tools/` to coverage scope; confirm
  project coverage ≥ 85% and every file ≤ 150 LOC; update `docs/PROGRESS.md`; note the
  TeX/pandoc prerequisite in `CLAUDE.md` if not already. (Satisfies §6.2/§3.2 gate;
  **DoD:** `uv run ruff check`, `uv run pytest -q`, `uv run pytest --cov` all green.)

- [x] **D16** — **Deliver the section-by-section Author** (the behaviour D8 + TBD-D6 were
  marked done for but never actually shipped). Today `config/tasks.yaml::writing_task` is a
  **single** Task → one LLM call → Gemini's output-token ceiling caps the live book at ~14
  pp instead of 30. Make the Author compose one section at a time over `section_outline()`
  and append each to `output/book.he.md`, so length scales without truncation. Inject a
  per-section length floor and `pages_per_section` into each section prompt from config —
  add `words_per_page` (or `min_words_per_section`) to `book.json` so nothing is hardcoded.
  Mechanism is the Developer's call (a `report/` writer loop driving `GatekeptLLM` per
  section is the simplest fit), but **every section call MUST stay on the gatekept LLM
  path** (§5.1) and the Typesetter chain must be unchanged downstream. (Satisfies FR-D4
  for real; **DoD:** a unit test with a mocked LLM that returns a stub per call asserts (a)
  exactly one call per outline section, (b) `book.he.md` contains every section heading in
  order, (c) the per-section word floor is read from `book.json` and injected into the
  prompt — not a literal in `.py`; `tests/integration/test_book_pipeline.py` stays green;
  every file ≤150 LOC; `ruff`/`pytest`/cov ≥85% green.)

- [x] **D17** — **Real AI-generated cover** (overrides TBD-D5's "one bundled raster"). Add a
  gatekept image-generation client in `gateway/` (e.g. `gateway/images.py`) that calls the
  image API (Gemini image / Imagen) through the **same** limiter/retry/telemetry/translate
  stack as `http.py`; model + endpoint from config, key from env, failures raised as the
  five-class gateway errors. A `report/` step builds the cover prompt from `book.json`
  (`topic`/`title`), generates the PNG into `assets/`, and `assemble.py` embeds it. Missing
  key ⇒ fall back to the existing bundled `assets/alyasmeen.png` (never crash the run). **No
  image API call anywhere outside `gateway/`** (frozen invariant §5.1). (Satisfies the
  "real picture" ask; **DoD:** unit tests mock the image client — no live call — and assert
  the provider arg routes through the gateway, the missing-key fallback returns the bundled
  asset, and `assemble.deterministic_block` embeds the produced file; no key/model id in any
  `.py`; gate green.)

- [x] **D15** — `[HUMAN]` Live run. Done: three separate Gemini keys (+ Serper) in `.env`,
  MiKTeX + pandoc + David font verified, `uv run run_crew` executed. The live research
  yielded 8 real sourced figures and a 20.9k-word compose; two gaps the run surfaced
  (unclosed ```json fence; verbatim overflow) were fixed (502a79c / ab29ee2) and
  `output/book.pdf` rebuilt offline from the live data. **DoD met:** Hebrew PDF renders
  **41 pp**, the generated cover, and a table + figure + funnel graph + equation panel.
  `flush()` telemetry recorded in `docs/PROGRESS.md` §11 (28 Gemini + 12 Serper calls, $0.00).

## Coverage matrix (§6 — every requirement has a test)

| Requirement | Step(s) | Test |
|---|---|---|
| FR-D1 | D1 | `tests/unit/test_gateway_llm.py::test_provider_from_gemini_model` |
| FR-D2 | D3 | `tests/unit/test_search_tool.py::test_routes_through_gateway` |
| FR-D3 | D4, D5 | `tests/unit/test_dataset.py::test_source_required` |
| FR-D4 | D8 | `tests/unit/test_author_task.py::test_output_is_hebrew_md` |
| FR-D5 | D6 | `tests/unit/test_economics.py::test_ltv_matches_fixture` |
| FR-D6 | D7 | `tests/unit/test_figures.py::test_snippets_carry_real_values` |
| FR-D7 | D9 | `tests/unit/test_template.py::test_font_token_substituted` |
| FR-D8 | D10, D11 | `tests/unit/test_render.py` · `tests/unit/test_compile.py` |
| FR-D9 | D12, D13 | `tests/integration/test_book_pipeline.py::test_full_chain` |
| R-AC1 | D13 | `test_book_pipeline.py::test_full_chain` |
| R-AC2 | D3 | `test_search_tool.py::test_missing_key_fallback` |
| R-AC3 | D7 | `test_figures.py::test_snippets_carry_real_values` |
| R-AC4 | D6 | `test_economics.py::test_ltv_matches_fixture` |
| R-AC5 | D10 | `test_render.py::test_pandoc_argv` |

## Locked decisions (defaults applied 2026-06-11 — Director may redline before D1)

- **TBD-D1 → LOCKED.** LLM = Gemini `gemini/gemini-2.0-flash`, free tier, key env
  `GEMINI_API_KEY`. OpenRouter/DeepSeek kept as a fallback in git history, not in config.
- **TBD-D2 → LOCKED.** Grounding = Serper.dev free tier via the existing gateway path.
  No key ⇒ LLM-only with a visible "נתונים לא מאומתים" (unverified data) banner. Never
  the default — grounding is preferred.
- **TBD-D3 → LOCKED.** Hebrew engine = XeLaTeX + `polyglossia` + `bidi`; font default
  **David** (Windows-bundled Hebrew serif, already installed), name from `book.json`.
  Director may swap to `FrankRuehl`, `Gisha`, `Arial`, etc. Binaries (`pandoc`/`xelatex`)
  are resolved from `book.json.bin` — not assumed on PATH.
- **TBD-D4 → LOCKED.** Markdown→LaTeX = `pandoc` (deterministic), wrapped by the
  Typesetter tool. The LLM never writes raw LaTeX.
- **TBD-D5 → LOCKED.** Graph = `pgfplots` from `data.json`; table = `booktabs`; the
  "image" requirement = **one** bundled raster asset via `\includegraphics`.
- **TBD-D6 → LOCKED.** Book length floor **≥ 30 pages** (`book.json.page_target = 30`,
  tunable). The Author composes section-by-section (ADR-D6) so the page count scales
  without hitting output-token truncation.

## Reminder

Once these TBDs are locked and you approve the triplet, `/relay-next` transcribes these
TODOs into code one step at a time, and `/relay-verify` holds each step to the Segal
§19.1 Table-5 gate (`ruff` · `pytest` · cov ≥ 85% · ≤150 LOC/file · no hardcoded values ·
no secrets · `uv`-only) before it pushes. Same drum as B and G.
