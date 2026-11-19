"""Standalone live Gemini connection diagnostic."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def classify_error(exc: Exception) -> str:
    """Return a safe category for a live API exception."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    message = str(exc).lower()
    if status in {401, 403} or "unauthenticated" in message:
        return "authentication"
    if status == 404 or "not found" in message:
        return "invalid_model"
    if status == 429 or "rate" in message or "quota" in message:
        return "quota_or_rate_limit"
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if status in {503, 504}:
        return "service_unavailable"
    if "network" in message or "connection" in message:
        return "network"
    return "api_error"


def main() -> int:
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("FAIL: python-dotenv is not installed")
        return 1

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()

    if not api_key:
        print("FAIL: GEMINI_API_KEY is missing or empty")
        return 1

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("FAIL: google-genai SDK could not be imported")
        return 1

    print("PASS: SDK import succeeded")
    print("PASS: API key is configured")
    print(f"Selected model: {model}")

    try:
        client = genai.Client(api_key=api_key)
        available = []
        for item in client.models.list():
            name = getattr(item, "name", "")
            methods = str(
                getattr(item, "supported_actions", None)
                or getattr(item, "supported_generation_methods", None)
                or ""
            )
            if "generateContent" in methods and "gemini" in name.lower():
                available.append(name)
        if model not in {name.rsplit("/", 1)[-1] for name in available}:
            print(
                "WARN: Selected model was not listed as available; "
                "continuing with one direct request"
            )
    except Exception as exc:
        print(f"FAIL: model discovery {classify_error(exc)}")
        return 1

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: PawPal connection test succeeded.",
            config=types.GenerateContentConfig(
                max_output_tokens=20,
                temperature=0,
                http_options=types.HttpOptions(timeout=30_000),
            ),
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            print("FAIL: Gemini returned an empty response")
            return 1
        print("SUCCESS: live Gemini request completed")
        return 0
    except Exception as exc:
        print(f"FAIL: live Gemini request {classify_error(exc)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
