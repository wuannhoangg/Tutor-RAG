from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.llm_config import LLMConfig


@dataclass
class ResolvedLLMConfig:
    provider: str
    api_key: Optional[str]
    base_url: Optional[str]
    model: str


def _clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_provider_name(provider: Optional[str]) -> str:
    raw = _clean_optional(provider) or "openai_compatible"
    key = raw.lower().replace("-", "_").replace(" ", "_")

    aliases = {
        "google": "google_ai",
        "google_ai": "google_ai",
        "gemini": "google_ai",
        "openai": "openai",
        "anthropic": "anthropic",
        "ollama": "ollama",
        "lm_studio": "lm_studio",
        "openai_compatible": "openai_compatible",
        "local_runtime": "openai_compatible",
    }
    return aliases.get(key, key)


def _normalize_model_identifier(provider: str, model: str) -> str:
    clean_model = (model or "").strip()
    if not clean_model:
        return clean_model

    if "/" in clean_model:
        return clean_model

    if provider == "google_ai":
        return f"gemini/{clean_model}"
    if provider == "openai":
        return f"openai/{clean_model}"
    if provider == "anthropic":
        return f"anthropic/{clean_model}"
    if provider == "ollama":
        return f"ollama/{clean_model}"

    # lm_studio / openai_compatible / custom gateways
    return clean_model


def resolve_llm_config(request_config: Optional[LLMConfig]) -> ResolvedLLMConfig:
    settings = get_settings()

    if request_config is None or request_config.mode == "platform_default":
        provider = _normalize_provider_name(settings.PLATFORM_LLM_PROVIDER)
        model = _normalize_model_identifier(provider, settings.PLATFORM_LLM_MODEL)

        return ResolvedLLMConfig(
            provider=provider,
            api_key=_clean_optional(settings.PLATFORM_LLM_API_KEY),
            base_url=_clean_optional(settings.PLATFORM_LLM_BASE_URL),
            model=model,
        )

    if request_config.mode == "byok":
        if not request_config.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BYOK mode requires api_key.",
            )
        if not request_config.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BYOK mode requires model.",
            )

        provider = _normalize_provider_name(request_config.provider or "openai_compatible")
        model = _normalize_model_identifier(provider, request_config.model)

        return ResolvedLLMConfig(
            provider=provider,
            api_key=_clean_optional(request_config.api_key),
            base_url=_clean_optional(request_config.base_url),
            model=model,
        )

    if request_config.mode == "local_runtime":
        if not request_config.base_url and _normalize_provider_name(request_config.provider) != "ollama":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="local_runtime mode requires base_url.",
            )
        if not request_config.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="local_runtime mode requires model.",
            )

        provider = _normalize_provider_name(request_config.provider or "openai_compatible")
        model = _normalize_model_identifier(provider, request_config.model)

        return ResolvedLLMConfig(
            provider=provider,
            api_key=_clean_optional(request_config.api_key),
            base_url=_clean_optional(request_config.base_url),
            model=model,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported llm mode: {request_config.mode}",
    )