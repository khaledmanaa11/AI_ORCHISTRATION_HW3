# PLAN — market_book

> Triplet: [PRD](PRD_market_book.md) · this · [TODO](TODO_market_book.md)

## Architecture (the pipeline)

```
 config/book.json ── inputs ──┐
                              ▼
        ┌──────────────────────────────────────────────┐
        │  Agent 1 · Researcher        (LLM: Gemini)   │
        │    tool: web_search(query)                   │
        │      └─ gateway.http_post(provider="serper") │  ← §5.1 egress seam
        │    → output/research.md  (+ sourced figures) │
        └──────────────────┬───────────────────────────┘
                           │  deterministic loader
                           ▼
                   output/data.json   (typed, every figure has a source)
                           │
        ┌──────────────────▼───────────────────────────┐
        │  Agent 2 · Author            (LLM: Gemini)   │
        │    → output/book.he.md  (Hebrew Markdown:     │
        │       abstract · sections · table · figure ·  │
        │       graph-data · equations)                 │
        └──────────────────┬───────────────────────────┘
                           │
        report/economics.py  →  proved equations (LaTeX + numeric, from data.json)
        report/figures.py     →  pgfplots graph + booktabs table (from data.json)
                           │
        ┌──────────────────▼───────────────────────────┐
        │  Agent 3 · Typesetter        (LLM: Gemini)   │
        │    tool: render_and_compile                   │
        │      ├─ report/render.py  : pandoc + template │  (local subprocess —
        │      │     book.he.md → book.he.tex           │   NOT an external API,
        │      └─ report/compile.py : xelatex           │   does not use the
        │            book.he.tex → book.pdf             │   gateway)
        └──────────────────┬───────────────────────────┘
                           ▼
                     output/book.pdf   (Hebrew, RTL)

 main.py: kickoff(inputs from book.json) → gateway.flush()  (token report §11)
```

Two egress rules hold simultaneously:
- **External API calls** (LLM completions, Serper search) → **always the gateway** (§5.1).
- **Local subprocesses** (`pandoc`, `xelatex`) → **not** the gateway (they leave no
  network); they get their own typed errors and config-driven flags.

## Public interface (stable contract)

```python
# tools/search.py
def web_search(query: str, *, max_results: int = 5) -> list[dict]: ...   # via gateway

# report/dataset.py
def load_dataset(research_md: Path) -> Path: ...        # research.md → data.json
def read_dataset(path: Path) -> Dataset: ...            # typed accessor

# report/economics.py
def equations(ds: Dataset) -> list[Equation]: ...       # .latex + .value each

# report/figures.py
def graph_snippet(ds: Dataset) -> str: ...              # pgfplots .tex
def table_snippet(ds: Dataset) -> str: ...              # booktabs .tex

# report/render.py
def markdown_to_latex(md: Path, tex: Path, *, template: Path) -> Path: ...

# report/compile.py
def compile_pdf(tex: Path) -> Path: ...                 # → book.pdf
```

Consumers catch only the gateway's five exception classes for network work, and a small
`TypesetError(RuntimeError)` for the local pandoc/xelatex steps.

## File layout (each ≤ 150 code lines, §3.2)

- `src/reasearch_crew/config/book.json` — topic, title, author, `language`, Hebrew font,
  page target, `pdf_engine`, output paths. (config, §7.2)
- `src/reasearch_crew/config/llm.json` — **edited**: Gemini model + `GEMINI_API_KEY`.
- `src/reasearch_crew/config/rate_limits.json` — **edited**: add a `gemini` provider.
- `src/reasearch_crew/tools/search.py` — `web_search` over `gateway.http_post` (~80).
- `src/reasearch_crew/report/dataset.py` — parse/validate sourced figures → `data.json`,
  typed `Dataset` accessor (~110).
- `src/reasearch_crew/report/economics.py` — equation set, each `.latex` + `.value`
  computed from `Dataset` (~120).
- `src/reasearch_crew/report/figures.py` — `pgfplots` + `booktabs` snippet builders (~110).
- `src/reasearch_crew/templates/book.he.tex` — XeLaTeX Hebrew template (not Python LOC).
- `src/reasearch_crew/report/render.py` — pandoc wrapper, typed errors (~80).
- `src/reasearch_crew/report/compile.py` — xelatex wrapper, typed errors (~80).
- `src/reasearch_crew/tools/typeset.py` — `render_and_compile` agent tool (~60).
- `src/reasearch_crew/config/agents.yaml` — **rewritten**: researcher · author · typesetter.
- `src/reasearch_crew/config/tasks.yaml` — **rewritten**: 3 tasks, Hebrew instructions.
- `src/reasearch_crew/crew.py` — **edited**: 3 agents/tasks, sequential wiring.
- `src/reasearch_crew/main.py` — **edited**: inputs from `book.json`, `flush()` after kickoff.
- `assets/` — at least one curated raster image embedded in the book.

Test layout (each ≤ 150 lines, all mock the LLM and the subprocesses):

- `tests/unit/test_search_tool.py` — routes through `http_post`; key-missing fallback.
- `tests/unit/test_dataset.py` — parse/validate; every figure requires a source.
- `tests/unit/test_economics.py` — numeric results vs hand-computed fixtures.
- `tests/unit/test_figures.py` — pgfplots/booktabs snippets carry the real values.
- `tests/unit/test_render.py` — pandoc argv (template + `--pdf-engine=xelatex`).
- `tests/unit/test_compile.py` — xelatex argv + `TypesetError` on non-zero exit.
- `tests/integration/test_book_pipeline.py` — full kickoff (mocked LLM + subprocess)
  yields the artifact chain ending at `book.pdf`.

## ADRs (decision · rationale · alternative)

- **ADR-D1 — Gemini free tier as the default LLM.**
  · Rationale: stable free key, strongest free Hebrew; cost $0. The gateway makes the
  swap a config edit (provider parsed from the `gemini/...` model prefix).
  · Rejected: OpenRouter `:free` — disappearing slugs (the B10 thrash), weaker Hebrew.

- **ADR-D2 — The LLM never authors LaTeX; typesetting is deterministic.**
  · Rationale: RTL Hebrew XeLaTeX is unforgiving; one bad token fails the compile. A
  fixed template + pandoc is reproducible and testable by argv.
  · Rejected: Author emits `.tex` directly — unverifiable, RTL-fragile.

- **ADR-D3 — Grounding through the *existing* gateway Serper path.**
  · Rationale: §5.1 already mandates one egress seam; `serper` is already in
  `rate_limits.json` and `http_post` already exists. Reuse, don't add a second client.
  · Rejected: a fresh `requests` client in the tool — a §5.1 violation.

- **ADR-D4 — Graph via `pgfplots`, table via `booktabs`, from `data.json`.**
  · Rationale: real numbers, text-defined, in-engine, diffable. One bundled raster
  asset satisfies the explicit "image" requirement separately.
  · Rejected: runtime matplotlib PNGs — extra step, binary artifact, no quality gain.

- **ADR-D5 — `data.json` is the single source of figures for prose, table, graph, and
  equations.** · Rationale: one set of numbers drives every representation, so the table,
  the plot, and the proved equations can never disagree. · Rejected: numbers re-stated
  per artifact — drift and contradiction.

- **ADR-D6 — A 30-page book is authored section-by-section, not in one LLM call.**
  · Rationale: a single completion cannot reliably emit ~30 pages of Hebrew before
  hitting output-token limits or degrading. The Author task iterates over a section
  outline (driven by `book.json.page_target`) and appends each section to `book.he.md`,
  so length scales without truncation. · Rejected: one giant `expected_output` — gets
  cut off mid-document and wastes the run.

## Concurrency / gatekeeper / config notes

- **Concurrency:** `Process.sequential` — one stage at a time; each agent's LLM calls and
  the Serper calls still pass the shared gateway limiter.
- **Gatekeeper (§5.1):** the search tool uses `gateway.http_post`; the LLM uses
  `GatekeptLLM` (unchanged). `pandoc`/`xelatex` are local subprocesses — explicitly out
  of the gateway's network scope, but they raise a typed `TypesetError`, never a raw
  `CalledProcessError`, to keep consumer error-handling uniform.
- **Config (§7.2):** `book.json` schema (v1.00):
  ```json
  {
    "version": "1.00",
    "topic": "ALYASMEEN — WhatsApp commerce agent for small businesses",
    "title": "מחקר שוק: אליאסמין",
    "author": "Khaled",
    "language": "he",
    "hebrew_font": "David",
    "page_target": 30,
    "pdf_engine": "xelatex",
    "bin": {
      "pandoc": "C:/Users/Hp/AppData/Local/Pandoc/pandoc.exe",
      "xelatex": "xelatex"
    },
    "paths": {
      "research_md": "output/research.md",
      "data_json": "output/data.json",
      "book_md": "output/book.he.md",
      "book_tex": "output/book.he.tex",
      "book_pdf": "output/book.pdf",
      "template": "templates/book.he.tex",
      "assets": "assets"
    }
  }
  ```
  `rate_limits.json` gains: `"gemini": { "rpm": 15, "tpm": 1000000, "burst": 5 }`
  (Google AI Studio free-tier flash defaults — tunable without code).

## Environment prerequisites (flagged for the Director — needed at D15 live run)

The deterministic typesetting path needs three things on the run machine — all already
present here, none cost money:

- **`xelatex`** — ✅ MiKTeX 25.12 installed (on PATH).
- **`pandoc`** — ✅ installed at `C:/Users/Hp/AppData/Local/Pandoc/pandoc.exe`. NOTE: it
  is **not on the global PATH** in fresh tool shells, so `render.py`/`compile.py` resolve
  the binary from `book.json.bin.{pandoc,xelatex}` (absolute path or bare name), never by
  assuming PATH. This keeps §7.2 satisfied and the run reproducible.
- **A Hebrew font** — ✅ `David` (Windows-bundled Hebrew serif) is the locked default;
  `FrankRuehl`, `Narkisim`, `Arial`, `Gisha` are also installed. The name lives in
  `book.json.hebrew_font`, not code.

Every D-step before D15 mocks these binaries, so the **gate stays green** regardless. The
`[HUMAN]` D15 live run uses the real binaries via the `book.json.bin` paths.
