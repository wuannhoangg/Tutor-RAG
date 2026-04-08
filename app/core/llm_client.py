import json
import httpx
from typing import Any, Dict, List, Optional
from app.core.config import get_settings
from app.core import logging

logger = logging.logger.getChild("llm_client")

class LLMClient:
    """
    Lightweight async LLM client supporting BYOK (Bring Your Own Key) and local Ollama.
    """
    def __init__(self, user_api_key: Optional[str] = None) -> None:
        self.settings = get_settings()
        
        # 1. Custom key từ user, 2. Key mặc định từ .env
        self.api_key = user_api_key or self.settings.LLM_API_KEY
        self.base_url = self.settings.LLM_BASE_URL
        self.model_name = self.settings.LLM_MODEL
        
        self.headers = {
            "Content-Type": "application/json"
        }
        # Nếu dùng API Key thật (không phải Ollama local) thì thêm header Authorization
        if self.api_key and self.api_key.lower() != "ollama":
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.0,
        json_mode: bool = False
    ) -> Optional[str]:
        """
        Send a request to the LLM. Returns text or None if it fails.
        """
        if not self.base_url or not self.model_name:
            logger.debug("LLM not fully configured. Bypassing.")
            return None

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as exc:
            logger.error("LLM API Error: %s - %s", exc.response.status_code, exc.response.text)
            return None
        except Exception as exc:
            logger.error("LLM call failed: %s. Falling back to deterministic logic.", exc)
            return None