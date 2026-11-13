"""LLM provider wrapper — supports Groq and Gemini via environment variables.
Set LLM_PROVIDER=groq  (default) or LLM_PROVIDER=gemini in your .env file.
"""
import os
import re
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent

# Lightweight .env loader so python-dotenv is not strictly required
ENV_FILE = ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_config():
    return {
        "provider": os.getenv("LLM_PROVIDER", "groq").lower(),
        "groq_key": os.getenv("GROQ_API_KEY", ""),
        "gemini_key": os.getenv("GEMINI_API_KEY", ""),
        "groq_model": os.getenv("GROQ_MODEL", "llama3-8b-8192"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    }


def _call_groq(messages: list[dict], system: str, cfg: dict) -> str:
    """Call Groq's OpenAI-compatible chat endpoint."""
    all_msgs = [{"role": "system", "content": system}] + messages
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {cfg['groq_key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": cfg["groq_model"],
            "messages": all_msgs,
            "temperature": 0.2,
            "max_tokens": 512,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(messages: list[dict], system: str, cfg: dict) -> str:
    """Call the Gemini generateContent endpoint."""
    user_text = "\n".join(m["content"] for m in messages if m["role"] == "user")
    combined = f"{system}\n\nUser question: {user_text}"
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{cfg['gemini_model']}:generateContent?key={cfg['gemini_key']}",
        json={
            "contents": [{"parts": [{"text": combined}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 512},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def chat(messages: list[dict], system: str) -> str:
    """Send messages to the configured LLM and return the reply text."""
    cfg = get_config()
    if not cfg["groq_key"] and not cfg["gemini_key"]:
        raise EnvironmentError(
            "No LLM API key found. Set GROQ_API_KEY or GEMINI_API_KEY in your .env file."
        )
    if cfg["provider"] == "gemini" or (not cfg["groq_key"] and cfg["gemini_key"]):
        return _call_gemini(messages, system, cfg)
    return _call_groq(messages, system, cfg)


def parse_llm_json(raw_text: str) -> dict:
    """Extract and parse JSON object containing answer, confidence, follow_up."""
    text = raw_text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        data = json.loads(text)
        return {
            "answer": data.get("answer", raw_text),
            "confidence": data.get("confidence", "medium"),
            "follow_up": data.get("follow_up", "Do you have any other questions about rail refunds?"),
        }
    except Exception:
        return {
            "answer": raw_text,
            "confidence": "medium",
            "follow_up": "Do you need clarification on any specific rule?",
        }


