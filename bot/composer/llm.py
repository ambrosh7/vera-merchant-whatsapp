"""LLM provider adapter — temperature=0, Groq-aware rate limits."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from bot import config
from bot.composer.rate_limit import RateLimitExceeded, get_rate_limiter

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _usage_total(resp: Any) -> Optional[int]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None
    total = getattr(usage, "total_tokens", None)
    if total is not None:
        return int(total)
    prompt = getattr(usage, "prompt_tokens", None) or 0
    completion = getattr(usage, "completion_tokens", None) or 0
    if prompt or completion:
        return int(prompt) + int(completion)
    return None


class LLMClient:
    def __init__(self) -> None:
        self.provider = (config.LLM_PROVIDER or "groq").lower()
        self.api_key = config.LLM_API_KEY or ""
        self.model = config.LLM_MODEL or ""

    @property
    def available(self) -> bool:
        if self.provider == "ollama":
            return True
        return bool(self.api_key)

    def complete_json(self, system: str, user: str, timeout: float = 20.0) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("LLM unavailable: set LLM_API_KEY")

        limiter = get_rate_limiter()
        max_out = int(config.LLM_MAX_OUTPUT_TOKENS)
        estimated = limiter.estimate_tokens(system, user, max_out)
        ok, reason = limiter.can_call(estimated)
        if not ok:
            snap = limiter.snapshot()
            logger.warning(
                "LLM skipped pre-flight (%s) snap=%s", reason, snap
            )
            raise RateLimitExceeded(f"LLM budget exceeded ({reason})")

        limiter.reserve(estimated)
        try:
            if self.provider in ("openai", "deepseek", "groq", "openrouter"):
                result, actual = self._openai_compatible(system, user, timeout, max_out)
            elif self.provider == "anthropic":
                result, actual = self._anthropic(system, user, timeout, max_out)
            elif self.provider == "gemini":
                result, actual = self._gemini(system, user, timeout, max_out)
            else:
                raise RuntimeError(f"Unsupported LLM_PROVIDER: {self.provider}")
            limiter.reconcile(estimated, actual)
            if actual is not None:
                logger.info(
                    "LLM ok model=%s est=%s actual=%s snap=%s",
                    self.model or self.provider,
                    estimated,
                    actual,
                    limiter.snapshot(),
                )
            return result
        except RateLimitExceeded:
            raise
        except Exception:
            # Reservation already counted; keep it so bursts don't retry-storm.
            raise

    def _openai_compatible(
        self, system: str, user: str, timeout: float, max_out: int
    ) -> tuple[dict[str, Any], Optional[int]]:
        from openai import OpenAI

        base_url = None
        model = self.model
        if self.provider == "deepseek":
            base_url = "https://api.deepseek.com"
            model = model or "deepseek-chat"
        elif self.provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            model = model or "openai/gpt-oss-120b"
        elif self.provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
            model = model or "openai/gpt-4o-mini"
        else:
            model = model or "gpt-4o-mini"

        client = OpenAI(api_key=self.api_key, base_url=base_url, timeout=timeout)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs: dict[str, Any] = {
            "model": model,
            "temperature": 0,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "max_tokens": max_out,
        }
        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as exc:
            msg = str(exc).lower()
            if "rate_limit" in msg or "429" in msg or "tokens per minute" in msg:
                raise RateLimitExceeded(f"provider rate limit: {exc}") from exc
            # gpt-oss sometimes fails strict json_object — retry once without it
            if "json_validate_failed" in msg or "failed to validate json" in msg:
                logger.warning("json_object failed; retrying without response_format")
                kwargs.pop("response_format", None)
                # Nudge the model again toward raw JSON
                kwargs["messages"] = messages + [
                    {
                        "role": "user",
                        "content": "Respond with a single compact JSON object only. No markdown.",
                    }
                ]
                try:
                    resp = client.chat.completions.create(**kwargs)
                except Exception as exc2:
                    msg2 = str(exc2).lower()
                    if "rate_limit" in msg2 or "429" in msg2:
                        raise RateLimitExceeded(f"provider rate limit: {exc2}") from exc2
                    raise
            else:
                raise
        content = resp.choices[0].message.content or ""
        if not content.strip():
            # Some reasoner models put draft text in reasoning
            reasoning = getattr(resp.choices[0].message, "reasoning", None)
            if reasoning:
                content = str(reasoning)
        if not content.strip():
            raise RuntimeError("LLM returned empty content")
        return _extract_json(content), _usage_total(resp)

    def _anthropic(
        self, system: str, user: str, timeout: float, max_out: int
    ) -> tuple[dict[str, Any], Optional[int]]:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key, timeout=timeout)
        model = self.model or "claude-sonnet-4-20250514"
        msg = client.messages.create(
            model=model,
            max_tokens=max_out,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content = "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )
        usage = getattr(msg, "usage", None)
        actual = None
        if usage is not None:
            actual = int(getattr(usage, "input_tokens", 0) or 0) + int(
                getattr(usage, "output_tokens", 0) or 0
            )
        return _extract_json(content), actual

    def _gemini(
        self, system: str, user: str, timeout: float, max_out: int
    ) -> tuple[dict[str, Any], Optional[int]]:
        import urllib.request

        model = self.model or "gemini-2.0-flash"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "maxOutputTokens": max_out,
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Gemini usage metadata optional
        um = data.get("usageMetadata") or {}
        actual = um.get("totalTokenCount")
        return _extract_json(text), int(actual) if actual is not None else None
