"""
Unified LLM Client — abstracts Anthropic Claude and OpenAI.

Priority:
  1. Anthropic Claude (if ANTHROPIC_API_KEY is set)
  2. OpenAI GPT (if OPENAI_API_KEY is set)

All NL2SQL, Semantic Engine, and Chat modules use this client.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    raw: Optional[Any] = None


class LLMClient:
    """
    Drop-in LLM abstraction. Auto-selects provider based on env vars.

    Usage:
        client = LLMClient()
        resp = client.chat(
            system="You are a SQL expert.",
            user="Write a query to get top customers.",
            max_tokens=500,
            json_mode=True,
        )
        print(resp.content)
    """

    def __init__(
        self,
        prefer: str = "auto",    # "auto" | "anthropic" | "openai"
        model_override: Optional[str] = None,
    ):
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._openai_key = os.getenv("OPENAI_API_KEY", "")
        self._prefer = prefer
        self._model_override = model_override
        self._provider = self._resolve_provider()
        logger.info(f"LLMClient initialized: provider={self._provider}")

    def _resolve_provider(self) -> str:
        if self._prefer == "anthropic" and self._anthropic_key:
            return "anthropic"
        if self._prefer == "openai" and self._openai_key:
            return "openai"
        if self._anthropic_key:
            return "anthropic"
        if self._openai_key:
            return "openai"
        raise RuntimeError(
            "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env"
        )

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def default_model(self) -> str:
        if self._model_override:
            return self._model_override
        return {
            "anthropic": "claude-haiku-4-5",  # fast + cheap for NL2SQL / routing
            "openai": "gpt-4o-mini",
        }[self._provider]

    @property
    def smart_model(self) -> str:
        """Larger model for complex reasoning tasks."""
        if self._model_override:
            return self._model_override
        return {
            "anthropic": "claude-haiku-4-5",   # use haiku for all tasks (low credit balance)
            "openai": "gpt-4o",
        }[self._provider]

    def chat(
        self,
        user: str,
        system: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        json_mode: bool = False,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send a chat message and return an LLMResponse.

        Args:
            user: User message content.
            system: System prompt (optional).
            history: Prior messages [{"role": "user"|"assistant", "content": "..."}].
            max_tokens: Max tokens to generate.
            temperature: Sampling temperature.
            json_mode: Ask the model to respond with valid JSON.
            model: Override the default model for this call.
        """
        if self._provider == "anthropic":
            return self._anthropic_chat(user, system, history, max_tokens, temperature, json_mode, model)
        return self._openai_chat(user, system, history, max_tokens, temperature, json_mode, model)

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------

    def _anthropic_chat(
        self, user, system, history, max_tokens, temperature, json_mode, model
    ) -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic not installed. Run: pip install anthropic")

        client = anthropic.Anthropic(api_key=self._anthropic_key)
        chosen_model = model or self.default_model

        messages = []
        for msg in (history or []):
            messages.append({"role": msg["role"], "content": msg["content"]})

        if json_mode:
            user = user + "\n\nRespond with valid JSON only — no markdown, no explanation outside the JSON."

        messages.append({"role": "user", "content": user})

        kwargs: Dict[str, Any] = {
            "model": chosen_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        content = response.content[0].text
        if json_mode:
            content = self._strip_markdown_fences(content)

        return LLMResponse(
            content=content,
            model=chosen_model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            raw=response,
        )

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Remove ```json ... ``` or ``` ... ``` wrappers from LLM responses."""
        import re
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def _openai_chat(
        self, user, system, history, max_tokens, temperature, json_mode, model
    ) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai not installed. Run: pip install openai")

        client = OpenAI(api_key=self._openai_key)
        chosen_model = model or self.default_model

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        for msg in (history or []):
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user})

        kwargs: Dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content

        return LLMResponse(
            content=content,
            model=chosen_model,
            provider="openai",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            raw=response,
        )
