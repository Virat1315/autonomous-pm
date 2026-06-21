"""
llm_client.py – Shared LLM client.
Supports OpenAI, Anthropic, and Google Gemini.
Set LLM_PROVIDER=openai | anthropic | gemini
"""
import os
import json
import logging
import httpx
from typing import Optional

logger = logging.getLogger("llm-client")

LLM_PROVIDER      = os.getenv("LLM_PROVIDER", "openai").lower()

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL      = os.getenv("OPENAI_MODEL", "gpt-4o")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL      = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")


async def call_llm(
    prompt: str,
    system: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    provider: Optional[str] = None,
) -> str:
    p = (provider or LLM_PROVIDER).lower()
    if p == "anthropic":
        return await _call_anthropic(prompt, system, temperature, max_tokens)
    if p == "gemini":
        return await _call_gemini(prompt, system, temperature, max_tokens)
    return await _call_openai(prompt, system, temperature, max_tokens)


async def _call_openai(prompt: str, system: str, temperature: float, max_tokens: int) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(prompt: str, system: str, temperature: float, max_tokens: int) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


async def _call_gemini(prompt: str, system: str, temperature: float, max_tokens: int) -> str:
    """
    Calls Google Gemini via the REST API (no SDK needed).
    Gemini doesn't have a separate system role in the same way —
    we prepend the system prompt into the first user turn.
    We also instruct it to return JSON since Gemini 1.5 Pro supports
    response_mime_type: application/json.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Combine system + user prompt (Gemini handles system via user turn)
    combined_prompt = f"{system}\n\n---\n\n{prompt}"

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": combined_prompt}]}
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",  # forces JSON output
        },
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        # Extract text from Gemini response structure
        return data["candidates"][0]["content"]["parts"][0]["text"]


def parse_json_response(raw: str) -> dict:
    """Strip accidental markdown fences and parse JSON."""
    clean = raw.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1]
        if clean.startswith("json"):
            clean = clean[4:]
    return json.loads(clean.strip())


def active_model() -> str:
    if LLM_PROVIDER == "anthropic":
        return ANTHROPIC_MODEL
    if LLM_PROVIDER == "gemini":
        return GEMINI_MODEL
    return OPENAI_MODEL
