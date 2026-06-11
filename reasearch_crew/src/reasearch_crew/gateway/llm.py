from __future__ import annotations

from typing import Any

from crewai import LLM

from . import rate_limiter, retry, telemetry
from .errors import from_provider_exception


def _provider_from_model(model: str) -> str:
    """Take 'openrouter/google/gemma...' → 'openrouter'."""
    if "/" in model:
        return model.split("/", 1)[0]
    return model


def _token_counts(response: Any) -> tuple[int, int]:
    """Best-effort extraction of (input, output) token totals from a response."""
    usage = None
    if isinstance(response, dict):
        usage = response.get("usage")
    else:
        usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    get = usage.get if isinstance(usage, dict) else lambda k, d=0: getattr(usage, k, d)
    return int(get("prompt_tokens", 0) or 0), int(get("completion_tokens", 0) or 0)


class GatekeptLLM(LLM):
    """crewai.LLM subclass that funnels every .call through the gateway.

    crewai's ``LLM.__new__`` is a factory: for a recognized native provider
    (e.g. ``gemini/...``) it returns a provider-specific completion object,
    NOT an ``LLM`` subclass — which would silently bypass this gateway. Forcing
    ``is_litellm=True`` keeps construction on the litellm path so the instance
    really is a ``GatekeptLLM`` and every call flows through ``.call`` below.
    """

    def __new__(cls, *args, **kwargs):
        kwargs["is_litellm"] = True
        return super().__new__(cls, *args, **kwargs)

    def _provider_name(self) -> str:
        return _provider_from_model(self.model)

    def call(self, messages, *args, **kwargs):
        provider = self._provider_name()
        rate_limiter.acquire(provider)
        attempts = {"n": 0}

        def _do():
            attempts["n"] += 1
            try:
                return super(GatekeptLLM, self).call(messages, *args, **kwargs)
            except Exception as exc:
                raise from_provider_exception(exc) from exc

        try:
            result = retry.run(provider, _do)
        finally:
            if attempts["n"] > 1:
                for _ in range(attempts["n"] - 1):
                    telemetry.record_retry(provider)

        in_tok, out_tok = _token_counts(result)
        telemetry.record_call(
            provider, input_tokens=in_tok, output_tokens=out_tok
        )
        return result

    def completion(self, *args, **kwargs):
        """Mirror .call for any code that adopts the litellm-shaped surface."""
        return self.call(*args, **kwargs)
