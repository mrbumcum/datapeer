import os
from typing import Literal, Optional

from dotenv import load_dotenv

load_dotenv()

ProviderName = Literal["openai", "claude", "gemini"]


def _normalize_provider(raw: Optional[str]) -> ProviderName:
    """
    Normalize arbitrary provider strings from the client into a canonical name.
    Defaults to 'openai' when unknown.
    """
    if not raw:
        return "openai"
    value = raw.strip().lower()
    if value in {"openai", "gpt-4o-mini", "gpt-4o", "gpt"}:
        return "openai"
    if value.startswith("claude"):
        return "claude"
    if value.startswith("gemini"):
        return "gemini"
    return "openai"


def get_active_provider_name(raw: Optional[str]) -> ProviderName:
    return _normalize_provider(raw)


def _ensure_openai_client():
    from openai import OpenAI

    api_key = os.getenv("OPEN_AI_API_KEY")
    if not api_key:
        raise ValueError("OPEN_AI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def _ensure_claude_client():
    import anthropic

    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def _ensure_gemini_client():
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)
    # The model handle is created per call; configuration is global
    return genai


async def complete_chat(
    provider: Optional[str],
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> str:
    """
    Provider-agnostic chat completion helper used for simple single-turn chats.
    More advanced flows (like OpenAI tools for quantitative analysis) remain
    implemented directly where needed.
    """
    normalized = get_active_provider_name(provider)

    if normalized == "openai":
        client = _ensure_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    if normalized == "claude":
        client = _ensure_claude_client()
        # Claude uses a single messages list with system content separated
        result = client.messages.create(
            model="claude-haiku-4-5-20251001",
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
        genai = _ensure_gemini_client()
        model = genai.GenerativeModel("gemini-3-flash-preview")
        prompt = f"{system_prompt}\n\nUser:\n{user_prompt}"
        result = model.generate_content(prompt)
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
    client = _ensure_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""

