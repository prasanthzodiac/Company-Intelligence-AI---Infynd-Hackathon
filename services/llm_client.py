"""
Unified LLM client for Ollama (local/remote) and OpenAI-compatible APIs (OpenAI, Groq, etc.).
Configure via config/settings.yaml and environment variables (see .env.example).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
DEFAULT_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


@dataclass
class LLMConfig:
    provider: str  # "ollama" | "openai"
    api_url: str
    model: str
    temperature: float = 0.0
    api_key: Optional[str] = None

    def is_local_ollama(self) -> bool:
        return self.provider == "ollama" and any(
            h in self.api_url for h in ("localhost", "127.0.0.1")
        )


def _infer_provider(api_url: str, explicit: Optional[str]) -> str:
    if explicit:
        return explicit.strip().lower()
    url = (api_url or "").lower()
    if "/v1/chat/completions" in url or "api.openai.com" in url:
        return "openai"
    if "/api/chat" in url or "ollama" in url or ":11434" in url:
        return "ollama"
    return "ollama"


def merge_llm_config(llm_yaml: Optional[Dict[str, Any]] = None) -> LLMConfig:
    """Merge settings.yaml `llm` block with environment variables (env wins)."""
    cfg = dict(llm_yaml or {})

    api_url = (
        os.environ.get("LLM_API_URL")
        or os.environ.get("OLLAMA_API_URL")
        or os.environ.get("OLLAMA_HOST")
        or cfg.get("api_url")
        or DEFAULT_OLLAMA_CHAT_URL
    )
    if api_url and not api_url.startswith("http"):
        api_url = f"http://{api_url.rstrip('/')}/api/chat"

    provider = _infer_provider(
        api_url,
        os.environ.get("LLM_PROVIDER") or cfg.get("provider"),
    )

    model = os.environ.get("LLM_MODEL") or cfg.get("model") or (
        "gpt-4o-mini" if provider == "openai" else "llama3"
    )

    temperature = float(
        os.environ.get("LLM_TEMPERATURE", cfg.get("temperature", 0.0))
    )

    api_key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or cfg.get("api_key")
        or ""
    )
    api_key = api_key.strip() or None

    if provider == "openai" and not api_url.endswith("/chat/completions"):
        if api_url.rstrip("/").endswith("/v1"):
            api_url = f"{api_url.rstrip('/')}/chat/completions"
        elif "/v1/" not in api_url:
            api_url = DEFAULT_OPENAI_CHAT_URL

    return LLMConfig(
        provider=provider,
        api_url=api_url.rstrip("/") if provider == "openai" else api_url,
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


def llm_config_to_dict(config: LLMConfig) -> Dict[str, Any]:
    return {
        "provider": config.provider,
        "api_url": config.api_url,
        "model": config.model,
        "temperature": config.temperature,
        "api_key": config.api_key or "",
    }


def recommended_llm_workers(config: LLMConfig, company_count: int, cpu_workers: int) -> int:
    env_max = os.environ.get("LLM_MAX_WORKERS")
    if env_max is not None and env_max.strip() != "":
        return max(1, min(int(env_max), company_count))
    if config.provider == "openai":
        return max(1, min(2, company_count))
    if config.is_local_ollama():
        return max(1, min(4, cpu_workers, company_count))
    return max(1, min(2, company_count))


def chat_completion(
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool = False,
    timeout: int = 600,
    max_tokens: Optional[int] = None,
) -> str:
    """Call configured LLM provider; returns assistant message text."""
    if config.provider == "openai":
        return _chat_openai(
            config,
            system_prompt,
            user_prompt,
            json_mode=json_mode,
            timeout=timeout,
            max_tokens=max_tokens,
        )
    return _chat_ollama(
        config,
        system_prompt,
        user_prompt,
        json_mode=json_mode,
        timeout=timeout,
        max_tokens=max_tokens,
    )


def check_llm_reachable(config: LLMConfig, timeout: int = 10) -> Dict[str, Any]:
    """Quick connectivity check for /api/health."""
    try:
        if config.provider == "openai":
            if not config.api_key:
                return {
                    "ok": False,
                    "provider": config.provider,
                    "error": "LLM_API_KEY or OPENAI_API_KEY is not set",
                }
            if os.environ.get("LLM_HEALTH_CHECK_FULL", "").lower() not in (
                "1",
                "true",
                "yes",
            ):
                return {
                    "ok": True,
                    "provider": config.provider,
                    "model": config.model,
                    "api_url": _redact_url(config.api_url),
                    "note": "API key set; set LLM_HEALTH_CHECK_FULL=true to ping the provider",
                }
            chat_completion(
                config,
                "You are a health check.",
                "Reply with exactly: ok",
                timeout=timeout,
                max_tokens=8,
            )
        else:
            base = config.api_url.split("/api/")[0]
            r = requests.get(f"{base}/api/tags", timeout=timeout)
            r.raise_for_status()
        return {
            "ok": True,
            "provider": config.provider,
            "model": config.model,
            "api_url": _redact_url(config.api_url),
        }
    except Exception as e:
        return {
            "ok": False,
            "provider": config.provider,
            "model": config.model,
            "api_url": _redact_url(config.api_url),
            "error": str(e),
        }


def _redact_url(url: str) -> str:
    if len(url) > 80:
        return url[:60] + "..."
    return url


def _chat_ollama(
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool,
    timeout: int,
    max_tokens: Optional[int],
) -> str:
    payload: Dict[str, Any] = {
        "model": config.model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": config.temperature},
    }
    if json_mode:
        payload["format"] = "json"
    if max_tokens is not None:
        payload["options"]["num_predict"] = max_tokens

    response = requests.post(config.api_url, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    content = ""
    if isinstance(data, dict):
        msg = data.get("message") or {}
        content = (msg.get("content") or "").strip()
    if not content:
        raise ValueError("Empty response from Ollama")
    return content


def _chat_openai(
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool,
    timeout: int,
    max_tokens: Optional[int],
) -> str:
    if not config.api_key:
        raise ValueError(
            "OpenAI-compatible provider requires LLM_API_KEY or OPENAI_API_KEY"
        )

    payload: Dict[str, Any] = {
        "model": config.model,
        "temperature": config.temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        config.api_url, json=payload, headers=headers, timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("Empty response from OpenAI-compatible API")
    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise ValueError("Empty response from OpenAI-compatible API")
    return content
