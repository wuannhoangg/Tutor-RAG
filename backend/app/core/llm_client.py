from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional

from litellm import acompletion

from app.core import logging
from app.core.provider_config import ResolvedLLMConfig

logger = logging.logger.getChild("llm_client")


class LLMClient:
    """
    Async LLM client powered by LiteLLM.
    Supports both normal completion and token streaming.
    """

    def __init__(self, resolved_config: ResolvedLLMConfig) -> None:
        self.provider = resolved_config.provider
        self.api_key = resolved_config.api_key
        self.base_url = (resolved_config.base_url or "").rstrip("/")
        self.model_name = resolved_config.model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        json_mode: bool = False,
    ) -> Optional[str]:
        if not self.model_name:
            logger.debug("LLM model is not configured. Bypassing.")
            return None

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "timeout": 180,
            "drop_params": True,
        }

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await acompletion(**kwargs)

            choices = getattr(response, "choices", None)
            if not choices and isinstance(response, dict):
                choices = response.get("choices")
            if not choices:
                logger.error("LLM response missing choices: %r", response)
                return None

            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            if message is None and isinstance(first_choice, dict):
                message = first_choice.get("message")
            if message is None:
                logger.error("LLM response missing message: %r", response)
                return None

            content = getattr(message, "content", None)
            if content is None and isinstance(message, dict):
                content = message.get("content")

            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if isinstance(item, dict):
                        parts.append(str(item.get("text", "")))
                    else:
                        parts.append(str(item))
                content = "".join(parts)

            if content is None:
                logger.error("LLM response missing content: %r", response)
                return None

            return str(content)

        except Exception as exc:
            logger.error(
                "LLM call failed provider=%s model=%s err=%r",
                self.provider,
                self.model_name,
                exc,
            )
            return None

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        """
        Stream text chunks from LiteLLM in OpenAI-style delta format.
        """
        if not self.model_name:
            logger.debug("LLM model is not configured. Bypassing stream.")
            return

        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "timeout": 120,
            "drop_params": True,
            "stream": True,
        }

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url

        try:
            stream = await acompletion(**kwargs)

            async for chunk in stream:
                choices = getattr(chunk, "choices", None)
                if not choices and isinstance(chunk, dict):
                    choices = chunk.get("choices")

                if not choices:
                    continue

                first_choice = choices[0]

                delta = getattr(first_choice, "delta", None)
                if delta is None and isinstance(first_choice, dict):
                    delta = first_choice.get("delta")

                content = None
                if delta is not None:
                    content = getattr(delta, "content", None)
                    if content is None and isinstance(delta, dict):
                        content = delta.get("content")

                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            text = item.get("text")
                            if text is not None:
                                yield str(text)
                        elif item is not None:
                            yield str(item)
                elif content is not None:
                    yield str(content)

        except Exception as exc:
            logger.error(
                "LLM streaming failed provider=%s model=%s err=%r",
                self.provider,
                self.model_name,
                exc,
            )
            raise