import io

import pytest

from reasearch_crew.gateway import telemetry


@pytest.fixture(autouse=True)
def _reset():
    telemetry.reset()
    yield
    telemetry.reset()


def test_record_call_increments_calls():
    telemetry.record_call("openrouter", input_tokens=10, output_tokens=5)
    snap = telemetry.snapshot()
    assert snap["openrouter"]["calls"] == 1
    assert snap["openrouter"]["input_tokens"] == 10
    assert snap["openrouter"]["output_tokens"] == 5


def test_snapshot_matches_calls():
    """R-AC5: 3 OpenRouter + 2 Anthropic calls reflected in snapshot."""
    for _ in range(3):
        telemetry.record_call("openrouter", input_tokens=4, output_tokens=2)
    for _ in range(2):
        telemetry.record_call("anthropic", input_tokens=7, output_tokens=3)

    snap = telemetry.snapshot()
    assert snap["openrouter"]["calls"] == 3
    assert snap["openrouter"]["input_tokens"] == 12
    assert snap["openrouter"]["output_tokens"] == 6
    assert snap["anthropic"]["calls"] == 2
    assert snap["anthropic"]["input_tokens"] == 14
    assert snap["anthropic"]["output_tokens"] == 6


def test_record_retry_increments_retries():
    telemetry.record_retry("openrouter")
    telemetry.record_retry("openrouter")
    snap = telemetry.snapshot()
    assert snap["openrouter"]["retries"] == 2
    assert snap["openrouter"]["calls"] == 0


def test_reset_clears_counters():
    telemetry.record_call("openrouter")
    telemetry.reset()
    assert telemetry.snapshot() == {}


def test_flush_prints_and_clears():
    telemetry.record_call("openrouter", input_tokens=1, output_tokens=2)
    buf = io.StringIO()
    returned = telemetry.flush(stream=buf)
    out = buf.getvalue()
    assert "gateway[openrouter]" in out
    assert "calls=1" in out
    assert returned["openrouter"]["calls"] == 1
    assert telemetry.snapshot() == {}


def test_flush_empty_prints_no_calls_recorded():
    buf = io.StringIO()
    telemetry.flush(stream=buf)
    assert "no calls recorded" in buf.getvalue()


def test_record_call_handles_none_tokens():
    telemetry.record_call("openrouter", input_tokens=None, output_tokens=None)
    snap = telemetry.snapshot()
    assert snap["openrouter"]["calls"] == 1
    assert snap["openrouter"]["input_tokens"] == 0
