import json
from groq import Groq
from app.config import get_settings

settings = get_settings()
_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def chat(prompt: str, *, json_mode: bool = False, temperature: float | None = None) -> str:
    """Single entry point for all Groq calls across all layers."""
    client = get_client()
    kwargs = {
        "model": settings.groq_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature if temperature is not None else settings.groq_temperature,
        "max_tokens": settings.groq_max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def chat_json(prompt: str) -> dict:
    """Chat + auto-parse JSON, with a single retry on malformed output."""
    raw = chat(prompt, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # one retry with explicit instruction
        retry_prompt = prompt + "\n\nReturn ONLY valid JSON. No markdown. No prose."
        raw = chat(retry_prompt, json_mode=True)
        return json.loads(raw)
