"""
Thin wrapper around an AI provider for the farming chatbot.

By default this calls the Anthropic Messages API using the
AI_PROVIDER_API_KEY / AI_PROVIDER_URL from config. If no API key is
configured, it falls back to a canned response so the endpoint still
works out of the box during development/testing.
"""

import requests
from flask import current_app

SYSTEM_PROMPT = (
    "You are an expert agricultural and solar-farming assistant. "
    "Give practical, concise, safe advice to farmers. If a question is "
    "outside farming/agriculture/solar topics, politely redirect the user."
)


def ask_ai_assistant(question: str) -> str:
    api_key = current_app.config.get("AI_PROVIDER_API_KEY")
    api_url = current_app.config.get("AI_PROVIDER_URL")

    if not api_key:
        return (
            "AI assistant is not configured yet. Please set AI_PROVIDER_API_KEY "
            "in your environment. (This is a placeholder response.) "
            f"You asked: '{question}'"
        )

    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": question}],
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        parts = [c["text"] for c in data.get("content", []) if c.get("type") == "text"]
        return "\n".join(parts).strip() or "Sorry, I couldn't generate a response."
    except requests.RequestException as exc:
        return f"AI assistant is temporarily unavailable ({exc}). Please try again later."
