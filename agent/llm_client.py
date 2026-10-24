"""OpenRouter LLM client integration for Supermarket Agent platform."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Lightweight robust .env loader without requiring external packages
def load_env_file(env_path: Path | None = None) -> None:
    """Load key-value pairs from .env into os.environ if not already present."""
    if env_path is None:
        env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        print(f"[WARN] Failed reading .env file: {e}")


# Load on module import
load_env_file()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.0-flash-001"


def get_api_key() -> str:
    """Retrieve the OpenRouter API key from environment."""
    load_env_file()
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def get_model() -> str:
    """Retrieve the model name from environment or return default."""
    return os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 1200) -> str | None:
    """Send chat completion request to OpenRouter API.
    
    Returns response content string if successful, or None if unavailable.
    """
    import requests

    api_key = get_api_key()
    if not api_key:
        return None

    model = get_model()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://supermarket-platform.local",
        "X-Title": "Supermarket Autonomous Stock Procurement Platform",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
            print(f"[WARN] OpenRouter unexpected response shape: {data}")
            return None
        else:
            print(f"[WARN] OpenRouter API error ({response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[WARN] Failed to connect to OpenRouter: {e}")
        return None


def call_llm_with_tools(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1500,
) -> dict[str, Any] | None:
    """Send chat completion request with tool-calling capabilities to OpenRouter.
    
    Returns full message dict: e.g. {"role": "assistant", "content": "...", "tool_calls": [...]}
    or None if unavailable.
    """
    import requests

    api_key = get_api_key()
    if not api_key:
        return None

    model = get_model()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://supermarket-platform.local",
        "X-Title": "Supermarket Autonomous Stock Procurement Platform",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"]
            return None
        else:
            print(f"[WARN] OpenRouter Tool API error ({response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[WARN] Failed to connect to OpenRouter: {e}")
        return None

