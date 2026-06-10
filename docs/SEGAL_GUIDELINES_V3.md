# Segal Guidelines V3.00 — working reference

*Guidelines for Writing Professional Software at the Highest Level of Excellence* — Dr. Yoram
Segal, V3.00 (2026-03-26). This is the standard every project in the course is graded against.
Below is a faithful working distillation; the authoritative source is the original PDF. Section
numbers (§) match the PDF so you can cite them in PRDs/PLANs the way the course expects.

> **§1.4 is the reason Relay exists.** The standard itself mandates the workflow: *act as a Senior
> Software Architect who orchestrates AI agents*, and **"the first rule of professional coding with
> AI is to define clear requirements and full documentation before every line of code."** Relay is
> the machine that enforces that rule.

---

## The gate — §19.1 Table 5 (the enforceable summary)

Every commit must satisfy all of these. This table is the spec for `/relay-verify`.

| Rule | Threshold | Enforced by |
|------|-----------|-------------|
| SDK architecture | all business logic reachable through the SDK layer | code review |
| OOP / no duplication | extract to mixin/base when logic repeats in 2+ places | code review |
| API Gatekeeper | every external API call goes through it | code review + test |
| Rate limiting | values from config, never hardcoded | config check |
| Queue management | overflow is queued, not dropped | integration test |
| Version control | starts at 1.00 | per-module version |
| TDD | Red → Green → Refactor | workflow |
| File size | **≤ 150 code lines per file** | automated check |
| Linter | **0 Ruff errors** | `ruff check` |
| Test coverage | **≥ 85%** | `pytest --cov` |
| Hardcoded values | **0 in source** | code review |
| Secrets | `.env-example` present, **0 secrets in code** | automated scan |
| Package manager | **everything through `uv`** | automated check |

---

## §1 — Professional software in the AI era
- **§1.3 SDLC:** 1) Requirements → `PRD`, 2) Planning & architecture → `PLAN` + `TODO`, 3) Development
  (TDD), 4) Testing (unit/integration/system), 5) Deployment, 6) Maintenance & improvement.
- **§1.4 The shift:** the engineer is a Senior Software Architect orchestrating multiple AI agents
  ("guided coding"). Up to ~16× productivity, but **only** when full requirements + documentation
  exist before any code. Otherwise agents produce maybe-working, non-professional code.

## §2 — Project structure & documentation (MANDATORY)
- **§2.1 `README.md` at root** — must read like a full user manual: Installation, Usage (CLI/GUI +
  workflow), Examples & screenshots, Configuration Guide, Contribution Guidelines, License & Credits.
- **§2.2 `docs/` is mandatory** and must contain:
  - `PRD.md` — context, user problem, audience, goals/KPIs/**acceptance criteria**, functional &
    non-functional requirements, user stories, use cases, constraints/dependencies/out-of-scope,
    timeline & milestones.
  - `PLAN.md` — C4 model, UML, **ADRs (decision + rationale + alternatives)**, API/interface/schema
    contracts.
  - `TODO.md` — atomic tasks with **priority + status**, phases with milestones, ownership,
    **definition of done per task**.
- **§2.3 Per-mechanism PRDs (CRITICAL):** every specific algorithm / central mechanism / complex
  component gets its **own** `docs/PRD_<mechanism>.md` (e.g. `PRD_authentication.md`,
  `PRD_search_engine.md`). Each covers: detailed description incl. theoretical background; specific
  I/O + performance metrics; constraints/limitations/alternatives considered; specific success
  criteria + test scenarios. *(This is the "triplet" pattern — `/relay-triplet` scaffolds it.)*
- **§2.4 Recommended layout:** `src/<pkg>/{sdk/sdk.py, services/, shared/{gatekeeper.py, config.py,
  version.py}, constants.py}` + `main.py`; `tests/{unit,integration}`; `docs/{PRD,PLAN,TODO,
  PRD_<mechanism>}`; `config/{setup.json, rate_limits.json}`; `data/ results/ assets/ notebooks/`;
  `README.md pyproject.toml uv.lock .env-example .gitignore`.
- **§2.5 Mandatory order:** PRD → PLAN → TODO → per-mechanism PRDs → **approve ALL docs before any
  development** → develop while updating TODO → save results + visualize + update README.

## §3 — Code documentation & structure
- **§3.1** Modular: layered or feature-based; clean separation of code / data / results / docs.
- **§3.2 The 150-line rule (HARD):** no code file exceeds **150 lines** (blanks & comments excluded).
  When it would, **split into more files — never compress code to fit.** Split strategies: helper
  function → own file; multiple responsibilities → mixin; read/write halves → 50/50 split; constants
  → `constants.py`; model definitions → own file.
- **§3.3** Docstrings on every function/module; comments say **why, not what**; DRY;
  single-responsibility; descriptive names; type hints.

## §4 — SDK architecture & OOP
- **§4.1 SDK layer:** ALL business logic reachable through one SDK entry point. Layers: External
  Consumers (GUI/CLI/REST/3rd-party) → **SDK** → Domain Services → Infrastructure. **No business
  logic in GUI/CLI/controllers.**
- **§4.2 OOP, zero duplication:** same body in 2+ files → shared module; same `try/except` in 3+ →
  wrapper; same logic with variations → base class / **mixin** (Template Method). Mixin rules: one
  concern each; don't override each other; independently testable.

## §5 — API Gatekeeper & rate control
- **§5.1** Every external API call goes through a central `ApiGatekeeper` — no direct calls bypass
  it. Limits checked before each call; overflow queued; all calls logged. Interface:
  `__init__(config: RateLimitConfig)`, `execute(api_call, *args, **kwargs)`, `get_queue_status()`.
- **§5.2** Rate-limit config read from `config/rate_limits.json` (never hardcoded):
  ```json
  { "rate_limits": { "version": "1.00", "services": { "default": {
      "requests_per_minute": 30, "requests_per_hour": 500,
      "concurrent_max": 5, "retry_after_seconds": 30, "max_retries": 3 } } } }
  ```
- **§5.3** FIFO queue, configured max depth, backpressure when full, refill as windows open.

## §6 — TDD & QA
- **§6.1 TDD:** Red → Green → Refactor. Every module has a test file; every public function ≥1 test;
  cover happy **and** error paths; tests written before/with code, not after. Mirror `src/` in
  `tests/`. Mock external deps; **test files are also ≤150 lines**; no test depends on a live service.
- **§6.2 Coverage ≥85%** (CI fails below):
  ```toml
  [tool.coverage.run]
  source = ["src"]
  omit = ["src/main.py", "*/tests/*", "src/**/gui/*"]
  [tool.coverage.report]
  fail_under = 85
  ```
- **§6.3** Edge cases documented (description + screenshot); clear errors, logging, graceful
  degradation. **§6.4** Document expected results per test; automated reports with pass/fail rates.

## §7 — Linting, config, security
- **§7.1 Ruff = 0 errors:**
  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py310"
  [tool.ruff.lint]
  select = ["E","F","W","I","N","UP","B","C4","SIM"]
  ignore = ["E501"]
  ```
- **§7.2 No hardcoded values** — all from config: `cfg.get("api_url")`, `cfg.get("rate_limit", 10)`,
  `cfg.get("timeout", 60)`, `os.environ.get("API_KEY")`. Allowed in code: physical/math constants,
  defaults, `constants.py`, `Enum`.
- **§7.3** `config/{setup.json, rate_limits.json, logging_config.json}`, `.env` (gitignored),
  `.env-example` (committed), `pyproject.toml`, `src/<pkg>/constants.py`.
- **§7.4 Secrets:** none in the repo. `.gitignore` must include `.env, *.key, *.pem,
  credentials.json`. `.env-example` with dummy values must exist. Secrets only via
  `os.environ.get(...)`. Rotate keys, monitor usage, least privilege.

## §8 — Versioning & uv
- **§8.1 Global versioning** starts at **1.00**, bumps on meaningful change. Required locations:
  `src/<pkg>/shared/version.py = 1.00`; JSON `"version": "1.00"`; `rate_limits.version = 1.00`. App
  validates config-version compatibility at startup.
- **§8.2** Meaningful commits, feature branches, PR review, tags for releases.
- **§8.3 `docs/PROMPTS.md`** — prompt-engineering log: context, goal, examples, iterations, lessons.
- **§8.4 `uv` is mandatory.** `uv sync` (not `pip install`), `uv add <pkg>`, `uv run python x.py`,
  `uv run pytest`, `uv lock`. **Forbidden: `pip`, `python -m`, `venv`, `virtualenv`.**
  `pyproject.toml` is the single source of truth (no `requirements.txt`); `uv.lock` is committed.

## §9 — Research & output analysis
- **§9.1** Sensitivity analysis — vary one parameter at a time (**OAT**), document each effect.
- **§9.2** Results-analysis **Jupyter notebook** is the central deliverable; LaTeX for formulas.
- **§9.3** High-quality visualization: bar/line/scatter/heatmap/box/waterfall as appropriate; good
  axis choice, accessible colors, detailed legends, clear labels, high resolution.

## §10 — UI/UX
- **§10.1** Quality: learnability, efficiency, memorability, error-prevention, satisfaction;
  Nielsen's 10 heuristics. **§10.2** Document each screen (screenshot + state), user workflows,
  interactions, accessibility.

## §11 — Costs
- **§11.1** Cost breakdown: input/output **token** counts per model, total cost; optimize tokens,
  batch, pick by cost/benefit. **§11.2** Forecast cost to scale, monitor real-time, **budget alerts**.

## §12 — Extension & maintenance
- **§12.1** Plugin architecture — clear extension points, lifecycle hooks, middleware, stable API.
  **§12.2** Maintainable: modular, separation of concerns, reusable components, testable.

## §13 — ISO/IEC 25010 quality
Functional suitability, performance efficiency, compatibility, usability, reliability, security,
maintainability, portability.

## §14 — Package organization
- **§14.1** `pyproject.toml` with name, version, author, license, deps. **§14.2** `__init__.py` in
  every package dir; export public API via `__all__` and set `__version__`. **§14.3** **Relative
  paths only** (relative to the package); never absolute. **§14.4** package self-check.

## §15 — Parallel & concurrent
- **§15.1** Multiprocessing = CPU-bound (heavy compute, models); multithreading = I/O-bound (network,
  DB, files). **§15.2** Thread safety: locks on shared state, `queue.Queue` for messaging, immutable
  messages, context managers. **§15.3** identify ops, right primitive, clean shutdown, no leaks.

## §16 — Building blocks
- **§16.1** Each block defines **Input / Output / Setup** data. **§16.2** Single responsibility,
  separation of concerns, reusability, testability. **§16.3** Document Input/Output/Setup in the
  class docstring; validate config and input.

## §17 — Final pre-submission checklist (the spec for `/relay-checklist`)
**17.1 Structure & docs:** root `README.md` (manual level); `docs/` has PRD+PLAN+TODO; per-mechanism
PRDs; architecture docs with clear diagrams; `PROMPTS.md` maintained.
**17.2 Architecture & code:** all logic via SDK; OOP, no duplication, mixins; all API calls via the
gatekeeper; rate limits from config; files ≤150 lines + docstrings; consistent style, descriptive
names.
**17.3 Testing & quality:** TDD (tests before/with code); coverage ≥85%; 0 Ruff errors; edge cases
documented; automated test reports.
**17.4 Config & security:** config separate from code, versioned; `.env-example` with dummy values;
no secrets/keys in code; `.gitignore` updated; uv as the only package manager; `pyproject.toml` +
`uv.lock` present.
**17.5 Research & viz:** parameter experiments; documented sensitivity analysis + analysis notebook;
quality figures, screenshots, architecture diagrams; token-cost analysis + optimization.
**17.6 Extension:** documented extension points; professional Python packaging; parallel processing
with thread safety; building-block design; ISO/IEC 25010; clean Git history with versioning,
license, deploy instructions.

## §18 — Standards referenced
MIT software-security, ISO/IEC 25010, Google engineering practices, Microsoft API guidelines,
Nielsen usability heuristics.
