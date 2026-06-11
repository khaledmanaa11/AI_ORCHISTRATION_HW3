from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from typing import IO


@dataclass
class Counters:
    calls: int = 0
    retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


_registry: dict[str, Counters] = {}


def _bucket(provider: str) -> Counters:
    c = _registry.get(provider)
    if c is None:
        c = Counters()
        _registry[provider] = c
    return c


def record_call(
    provider: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    c = _bucket(provider)
    c.calls += 1
    c.input_tokens += int(input_tokens or 0)
    c.output_tokens += int(output_tokens or 0)


def record_retry(provider: str) -> None:
    _bucket(provider).retries += 1


def snapshot() -> dict[str, dict[str, int]]:
    return {name: asdict(c) for name, c in _registry.items()}


def reset() -> None:
    _registry.clear()


def flush(stream: IO[str] | None = None) -> dict[str, dict[str, int]]:
    """Print a one-line summary per provider, then reset counters."""
    out = stream if stream is not None else sys.stdout
    snap = snapshot()
    if not snap:
        print("gateway: no calls recorded", file=out)
    for name, c in snap.items():
        print(
            f"gateway[{name}]: calls={c['calls']} retries={c['retries']} "
            f"in_tokens={c['input_tokens']} out_tokens={c['output_tokens']}",
            file=out,
        )
    reset()
    return snap
