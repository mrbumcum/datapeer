from __future__ import annotations

import asyncio
import os
from typing import Literal, Optional

from dotenv import load_dotenv

load_dotenv()

ProviderName = Literal["openai", "claude", "gemini"]

# Canonical text LLM models per provider.
# IDs and aliases are taken from the providers' public model overviews:
# - Claude: https://platform.claude.com/docs/en/about-claude/models/overview
# - Gemini: https://ai.google.dev/gemini-api/docs/models
# - OpenAI: https://developers.openai.com/api/docs/models

OPENAI_TEXT_MODELS: dict[str, str] = {
    # Frontier and cost-optimised text models
    "gpt-5.4": "gpt-5.4",
    "gpt-5-mini-2025-08-07": "gpt-5-mini-2025-08-07",
}

CLAUDE_TEXT_MODELS: dict[str, str] = {
    # Latest generation
    "claude-opus-4-6": "claude-opus-4-6",
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001": "claude-haiku-4-5-20251001",
    "claude-haiku-4-5": "claude-haiku-4-5-20251001",
    # Legacy but still available
    "claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
    "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20251101": "claude-opus-4-5-20251101",
    "claude-opus-4-5": "claude-opus-4-5-20251101",
    "claude-opus-4-1-20250805": "claude-opus-4-1-20250805",
    "claude-opus-4-1": "claude-opus-4-1-20250805",
    "claude-sonnet-4-20250514": "claude-sonnet-4-20250514",
    "claude-sonnet-4-0": "claude-sonnet-4-20250514",
    "claude-opus-4-20250514": "claude-opus-4-20250514",
    "claude-opus-4-0": "claude-opus-4-20250514",
    "claude-3-haiku-20240307": "claude-3-haiku-20240307",
}

GEMINI_TEXT_MODELS: dict[str, str] = {
    # Gemini 3 family
    "gemini-3.1-pro": "gemini-3.1-pro",
    "gemini-3-flash": "gemini-3-flash",
    "gemini-3-flash-preview": "gemini-3-flash-preview",
    "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
    # Gemini 2.5 family
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
    "gemini-2.5-pro": "gemini-2.5-pro",
}

# Cheapest known text models per provider (input token pricing).
DEFAULT_TEXT_MODEL_BY_PROVIDER: dict[ProviderName, str] = {
    # OpenAI: gpt-5-mini is cheaper than gpt-5.4
    "openai": "gpt-5-mini-2025-08-07",
    # Claude: Haiku has lowest price among Claude text models
    "claude": "claude-haiku-4-5-20251001",
    # Gemini: Flash-Lite is the budget-friendly text model
    "gemini": "gemini-2.5-flash-lite",
}

GLOBAL_DEFAULT_PROVIDER: ProviderName = "openai"


def _normalize_provider(raw: Optional[str]) -> ProviderName:
    """
    Normalize arbitrary provider strings from the client into a canonical name.
    Defaults to 'openai' when unknown.
    """
    if not raw:
        return GLOBAL_DEFAULT_PROVIDER
    value = raw.strip().lower()
    if value in {"openai", "gpt-4o-mini", "gpt-4o", "gpt"}:
        return "openai"
    if value.startswith("claude"):
        return "claude"
    if value.startswith("gemini"):
        return "gemini"
    return GLOBAL_DEFAULT_PROVIDER


def get_active_provider_name(raw: Optional[str]) -> ProviderName:
    return _normalize_provider(raw)


def _normalize_model(provider: ProviderName, model: Optional[str]) -> str:
    """
    Return a concrete model identifier for the given provider.
    Falls back to that provider's cheapest default when model is missing or unknown.
    """
    if provider == "openai":
        if model and model in OPENAI_TEXT_MODELS:
            return OPENAI_TEXT_MODELS[model]
        return OPENAI_TEXT_MODELS[DEFAULT_TEXT_MODEL_BY_PROVIDER["openai"]]

    if provider == "claude":
        if model and model in CLAUDE_TEXT_MODELS:
            return CLAUDE_TEXT_MODELS[model]
        return CLAUDE_TEXT_MODELS[DEFAULT_TEXT_MODEL_BY_PROVIDER["claude"]]

    if provider == "gemini":
        if model and model in GEMINI_TEXT_MODELS:
            return GEMINI_TEXT_MODELS[model]
        return GEMINI_TEXT_MODELS[DEFAULT_TEXT_MODEL_BY_PROVIDER["gemini"]]

    # Safety fallback: treat as OpenAI
    return OPENAI_TEXT_MODELS[DEFAULT_TEXT_MODEL_BY_PROVIDER["openai"]]


def _ensure_openai_client():
    from openai import OpenAI

    api_key = (
        os.getenv("OPEN_AI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_KEY")
    )
    if not api_key:
        raise ValueError(
            "OpenAI API key not set. Expected one of: OPEN_AI_API_KEY, OPENAI_API_KEY, OPENAI_KEY"
        )

    # Defensive cleanup for dotenv formats like KEY="...".
    api_key = api_key.strip().strip('"').strip("'")

    timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "60"))
    max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
    return OpenAI(api_key=api_key, timeout=timeout_s, max_retries=max_retries)


def _openai_single_turn_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    Synchronous OpenAI call that returns plain text.
    Uses the Responses API first (required for newer model families), and falls
    back to Chat Completions for older models.
    """
    client = _ensure_openai_client()

    def _supports_temperature(m: str) -> bool:
        # Some models (notably GPT-5 family) currently only support the default
        # temperature value. Passing anything else yields a 400.
        m = (m or "").strip().lower()
        if m.startswith("gpt-5"):
            return False
        return True

    # Prefer Responses API (supports GPT-5 per OpenAI model docs).
    try:
        kwargs: dict = {}
        if _supports_temperature(model) and temperature != 1:
            kwargs["temperature"] = temperature
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=max_tokens,
            **kwargs,
        )
        text = getattr(resp, "output_text", None)
        if text is None:
            # Some SDK versions return output via resp.output[*].content[*].text.
            output = getattr(resp, "output", []) or []
            parts: list[str] = []
            for item in output:
                for c in getattr(item, "content", []) or []:
                    t = getattr(c, "text", None)
                    if t:
                        parts.append(t)
            text = "\n".join(parts)
        return (text or "").strip()
    except Exception:
        pass

    # Fallback: Chat Completions API.
    # Note: some newer OpenAI models reject `max_tokens` and require
    # `max_completion_tokens` instead.
    kwargs2: dict = {}
    if _supports_temperature(model) and temperature != 1:
        kwargs2["temperature"] = temperature
    resp2 = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=max_tokens,
        **kwargs2,
    )
    return (resp2.choices[0].message.content or "").strip()


def _ensure_claude_client():
    import anthropic

    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def _ensure_gemini_client():
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    # New Google GenAI client; lightweight to construct per call.
    return genai.Client(api_key=api_key)


async def complete_chat(
    provider: Optional[str],
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> str:
    """
    Provider-agnostic chat completion helper used for simple single-turn chats.
    More advanced flows (like OpenAI tools for quantitative analysis) remain
    implemented directly where needed.
    """
    normalized = get_active_provider_name(provider)
    resolved_model = _normalize_model(normalized, model)

    if normalized == "openai":
        # Run the sync SDK call off the event loop to avoid "hanging" FastAPI.
        return await asyncio.to_thread(
            _openai_single_turn_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=resolved_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if normalized == "claude":
        client = _ensure_claude_client()
        # Claude uses a single messages list with system content separated
        result = client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )
        # Claude responses expose content as a list of blocks
        text_parts = []
        for block in getattr(result, "content", []) or []:
            if getattr(block, "type", None) == "text":
                text_parts.append(getattr(block, "text", ""))
        return "\n".join([p for p in text_parts if p]).strip()

    if normalized == "gemini":
        client = _ensure_gemini_client()
        prompt = f"{system_prompt}\n\nUser:\n{user_prompt}"
        result = client.models.generate_content(
            model=resolved_model,
            contents=prompt,
        )
        text = getattr(result, "text", None)
        if text:
            return text.strip()
        # Fallback: aggregate from candidates/parts if present
        candidates = getattr(result, "candidates", []) or []
        parts: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    parts.append(part_text)
        return "\n".join(parts).strip()

    # Fallback to OpenAI for any unexpected cases
    return await asyncio.to_thread(
        _openai_single_turn_text,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=_normalize_model("openai", model),
        temperature=temperature,
        max_tokens=max_tokens,
    )

