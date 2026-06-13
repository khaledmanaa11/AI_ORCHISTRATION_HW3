from __future__ import annotations

import re

# Fenced classes the Author sometimes invents. The real table, graph, figure
# and equations are injected deterministically (ADR-D2), so any LLM-authored
# copy is a duplicate that leaks as raw text — we strip them defensively.
_LEAK_CLASSES = frozenset(
    {
        "table", "graph", "chart", "figure", "figures", "json",
        "latex", "math", "mermaid", "tex", "code",
    }
)
# Markers that begin the deterministic tail; cutting here keeps re-runs
# idempotent (assemble appends the block, so it must not already be present).
_TAIL_MARKERS = ("## נתוני שוק", "# לוח נתונים")
_FENCE = re.compile(r"^([`~]{3,})\s*([^\s`~]*)")
# A markdown table delimiter row, e.g. ``| :--- | ---: |`` — its presence in a
# block of pipe lines marks a table the Author was told not to write (the real
# one is deterministic), so we drop the whole block.
_DELIM = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*$")


def _drop_leading_h1(text: str) -> str:
    """Drop a leaked leading H1 (filename or title). The contract is prose that
    starts at ``## ``; a single top H1 would nest every section beneath it."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if re.match(r"^#\s+\S", line.strip()) and not line.strip().startswith("##"):
            del lines[i]
        break
    return "\n".join(lines)


# Standalone caption / cross-reference lines that point at the deterministic
# figures (e.g. ``**טבלת 1: ...**`` or ``ראו איור 2``). The Author was told not
# to reference them; any survivor is orphaned once the figure block is stripped.
_CAPTION = re.compile(
    r"^\**\s*(טבל[הת]|תרשים|איור|גרף)\s+\d+\s*[:：].*$"
)
_SEE_REF = re.compile(r"^\(?\s*רא[הו]\s+(איור|תרשים|טבל[הת]|גרף)\b.*$")


def _strip_artifact_captions(text: str) -> str:
    """Remove orphaned figure/table caption and ``see figure N`` lines."""
    kept = [
        ln for ln in text.splitlines()
        if not (_CAPTION.match(ln.strip()) or _SEE_REF.match(ln.strip()))
    ]
    return "\n".join(kept)


def _unwrap_outer_markdown(text: str) -> str:
    """Unwrap a whole document fenced as ```markdown ... ```."""
    stripped = text.strip()
    if stripped.startswith("```markdown") or stripped.startswith("~~~markdown"):
        stripped = re.sub(r"^[`~]{3,}\s*markdown\s*\n", "", stripped, count=1)
        stripped = re.sub(r"\n[`~]{3,}\s*$", "", stripped, count=1)
    return stripped


def _dedent_prose(text: str) -> str:
    """Strip leading indentation so pandoc never reads prose as a code block.

    The Author routinely nests bullets four spaces deep (``    *   ``); pandoc
    turns any four-plus-space-indented line into a verbatim block, which then
    renders unwrapped and runs off both page margins. Flattening the indent
    keeps the bullets as ordinary list items that wrap normally."""
    return "\n".join(line.lstrip() for line in text.splitlines())


def _strip_leak_fences(text: str) -> str:
    """Drop fenced blocks: artifact classes go entirely, the rest is unwrapped.

    The book is pure prose, so no code fence should survive. A fence tagged with
    a deterministic-artifact class (table/json/latex…) is a leaked duplicate, so
    its markers AND body are dropped. Any other fence — a bare ``` or an unknown
    language — is just mis-fenced prose: drop only the markers and keep the text
    so it wraps, instead of becoming a verbatim block that runs off the page (a
    dangling bare fence would also swallow the deterministic tail as raw text)."""
    out: list[str] = []
    fence: str | None = None
    dropping = False
    for line in text.splitlines():
        match = _FENCE.match(line.strip())
        if fence is None and match:
            ticks, info = match.group(1), match.group(2).strip("{}=").lower()
            fence = ticks[0] * 3
            dropping = info in _LEAK_CLASSES
            continue
        if fence is not None and line.strip().startswith(fence):
            fence = None
            dropping = False
            continue
        if not dropping:
            out.append(line)
    return "\n".join(out)


def _is_pipe_table(block: str) -> bool:
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    has_delim = any("|" in ln and _DELIM.match(ln) for ln in lines)
    mostly_piped = sum("|" in ln for ln in lines) >= len(lines) - 1
    return has_delim and mostly_piped


def _strip_pipe_tables(text: str) -> str:
    """Drop raw markdown pipe tables the Author leaked into the prose."""
    blocks = re.split(r"\n[ \t]*\n", text)
    return "\n\n".join(b for b in blocks if not _is_pipe_table(b))


def _cut_deterministic_tail(text: str) -> str:
    """Drop a previously appended deterministic block so re-runs stay clean."""
    cuts = [text.find(m) for m in _TAIL_MARKERS if m in text]
    return text[: min(cuts)].rstrip() if cuts else text


def _drop_empty_headings(text: str) -> str:
    """Drop headings with no title text (a bare ``#``) that would otherwise
    render as an empty, numbered section."""
    return "\n".join(
        ln for ln in text.splitlines() if not re.match(r"^#{1,6}\s*$", ln)
    )


def _strip_heading_numbers(text: str) -> str:
    """Remove literal enumerators the Author typed into headings (``# 1. מבוא``,
    ``## 3.1. TAM``) so LaTeX is the single source of section numbering."""
    numbered = re.compile(r"^(#{1,6})\s+\d+(?:\.\d+)*[.)]?\s+(\S.*)$")
    out = [
        f"{m.group(1)} {m.group(2)}" if (m := numbered.match(ln)) else ln
        for ln in text.splitlines()
    ]
    return "\n".join(out)


def _normalize_heading_levels(text: str) -> str:
    """Promote headings so the shallowest becomes a level-1 section, giving
    clean top-level numbering (1, 2, 3…) however deep the Author nested them."""
    heads = re.compile(r"^(#{1,6})\s")
    depths = [len(m.group(1)) for ln in text.splitlines() if (m := heads.match(ln))]
    shift = min(depths) - 1 if depths else 0
    if shift <= 0:
        return text
    out = []
    for ln in text.splitlines():
        m = heads.match(ln)
        out.append("#" * (len(m.group(1)) - shift) + ln[len(m.group(1)):] if m else ln)
    return "\n".join(out)


def clean_narrative(text: str) -> str:
    """Return the Author's prose with leaked artifacts and duplicates removed.

    Order matters: cut any prior deterministic tail first, unwrap an outer
    ```markdown fence, dedent so no prose is read as code, drop a leaked
    filename heading, then strip invented table/graph/json fences. The result
    is pure narrative ready for assembly.
    """
    text = _cut_deterministic_tail(text)
    text = _unwrap_outer_markdown(text)
    text = _dedent_prose(text)
    text = _drop_leading_h1(text)
    text = _strip_leak_fences(text)
    text = _strip_pipe_tables(text)
    text = _strip_artifact_captions(text)
    text = _drop_empty_headings(text)
    text = _strip_heading_numbers(text)
    text = _normalize_heading_levels(text)
    return text.strip() + "\n"
