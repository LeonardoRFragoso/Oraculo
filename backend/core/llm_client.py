"""
Unified LLM Client — abstracts Anthropic Claude, OpenAI, OpenCode Zen and Z.AI.

Priority:
  1. Anthropic Claude (if ANTHROPIC_API_KEY is set)
  2. OpenAI GPT (if OPENAI_API_KEY is set)
  3. OpenCode Zen (if OPENCODE_API_KEY is set)
  4. Z.AI (if ZAI_API_KEY is set)

Use LLM_PROVIDER=opencode or LLM_PROVIDER=zai to force a provider.
All NL2SQL, Semantic Engine, and Chat modules use this client.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .model_config import active_model
from .plan_config import is_model_allowed, get_default_provider, get_allowed_models

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

    OpenCode Zen is exposed via the OpenAI-compatible endpoint
    https://opencode.ai/zen/v1 using model ids like ``opencode/<model-id>``.

    Z.AI is exposed via https://api.z.ai/api/paas/v4 using model ids like ``glm-4.5``.

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
        prefer: str = "auto",    # "auto" | "anthropic" | "openai" | "opencode" | "zai"
        model_override: Optional[str] = None,
        user_plan: str = "free",
        user_model: Optional[str] = None,
        user_provider: Optional[str] = None,
    ):
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._openai_key = os.getenv("OPENAI_API_KEY", "")
        self._opencode_key = os.getenv("OPENCODE_API_KEY", "")
        self._opencode_base_url = os.getenv(
            "OPENCODE_BASE_URL", "https://opencode.ai/zen/v1"
        )
        self._zai_key = os.getenv("ZAI_API_KEY", "")
        self._zai_base_url = os.getenv(
            "ZAI_BASE_URL", "https://api.z.ai/api/paas/v4"
        )
        self._user_plan = user_plan
        self._user_model = user_model
        self._user_provider = user_provider

        # If user has a specific provider preference, use it
        if user_provider and user_provider != "auto":
            self._prefer = user_provider
        else:
            self._prefer = os.getenv("LLM_PROVIDER", prefer)

        # If user has a specific model, validate it against their plan
        if user_model:
            provider_for_model = self._infer_provider_from_model(user_model)
            if is_model_allowed(user_plan, provider_for_model, user_model):
                self._model_override = user_model
            else:
                logger.warning(
                    f"Model '{user_model}' not allowed for plan '{user_plan}', "
                    f"falling back to plan default"
                )
                self._model_override = self._best_model_for_plan(user_plan, provider_for_model)
        else:
            self._model_override = model_override

        self._provider = self._resolve_provider()
        logger.info(f"LLMClient initialized: provider={self._provider}, plan={user_plan}, model={self._model_override or 'default'}")

    def _resolve_provider(self) -> str:
        if self._prefer == "anthropic" and self._anthropic_key:
            return "anthropic"
        if self._prefer == "openai" and self._openai_key:
            return "openai"
        if self._prefer == "opencode" and self._opencode_key:
            return "opencode"
        if self._prefer == "zai" and self._zai_key:
            return "zai"
        if self._anthropic_key:
            return "anthropic"
        if self._openai_key:
            return "openai"
        if self._opencode_key:
            return "opencode"
        if self._zai_key:
            return "zai"
        if self._prefer and self._prefer != "auto":
            logger.warning(
                f"LLM_PROVIDER={self._prefer} was requested but no matching key was found"
            )
        logger.warning(
            "No LLM API key found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, "
            "OPENCODE_API_KEY or ZAI_API_KEY in .env. Chat will be unavailable until then."
        )
        return "none"

    @staticmethod
    def _infer_provider_from_model(model_id: str) -> str:
        """Infers the provider from the model id prefix."""
        if model_id.startswith("opencode/"):
            return "opencode"
        if model_id.startswith("glm-"):
            return "zai"
        if model_id.startswith("claude-"):
            return "anthropic"
        if model_id.startswith("gpt-"):
            return "openai"
        return "zai"

    def _best_model_for_plan(self, plan: str, provider: str) -> Optional[str]:
        """Returns the best (first) allowed model for the plan and provider."""
        allowed = get_allowed_models(plan, provider)
        return allowed[0] if allowed else None

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def default_model(self) -> str:
        if self._model_override:
            return self._model_override
        if active_model.get():
            return active_model.get()
        if self._provider == "none":
            raise RuntimeError("No LLM provider configured.")
        return {
            "anthropic": "claude-haiku-4-5",  # fast + cheap for NL2SQL / routing
            "openai": "gpt-4o-mini",
            "opencode": "opencode/deepseek-v4-flash-free",  # free, fast
            "zai": "glm-4.5-flash",  # free, fast
        }[self._provider]

    @property
    def smart_model(self) -> str:
        """Larger model for complex reasoning tasks."""
        if self._model_override:
            return self._model_override
        if active_model.get():
            return active_model.get()
        if self._provider == "none":
            raise RuntimeError("No LLM provider configured.")
        return {
            "anthropic": "claude-haiku-4-5",   # use haiku for all tasks (low credit balance)
            "openai": "gpt-4o",
            "opencode": "opencode/big-pickle",  # free, strong reasoning
            "zai": "glm-4.5",  # strong reasoning
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
        if self._provider == "none":
            raise RuntimeError(
                "No LLM provider configured. "
                "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENCODE_API_KEY or ZAI_API_KEY in .env"
            )
        if self._provider == "anthropic":
            return self._anthropic_chat(user, system, history, max_tokens, temperature, json_mode, model)
        if self._provider == "opencode":
            return self._opencode_chat(user, system, history, max_tokens, temperature, json_mode, model)
        if self._provider == "zai":
            return self._zai_chat(user, system, history, max_tokens, temperature, json_mode, model)
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
        return self._openai_compatible_chat(
            user,
            system,
            history,
            max_tokens,
            temperature,
            json_mode,
            model,
            api_key=self._openai_key,
            base_url=None,
            provider="openai",
        )

    def _opencode_chat(
        self, user, system, history, max_tokens, temperature, json_mode, model
    ) -> LLMResponse:
        return self._openai_compatible_chat(
            user,
            system,
            history,
            max_tokens,
            temperature,
            json_mode,
            model,
            api_key=self._opencode_key,
            base_url=self._opencode_base_url,
            provider="opencode",
        )

    def _zai_chat(
        self, user, system, history, max_tokens, temperature, json_mode, model
    ) -> LLMResponse:
        return self._openai_compatible_chat(
            user,
            system,
            history,
            max_tokens,
            temperature,
            json_mode,
            model,
            api_key=self._zai_key,
            base_url=self._zai_base_url,
            provider="zai",
        )

    def _openai_compatible_chat(
        self,
        user,
        system,
        history,
        max_tokens,
        temperature,
        json_mode,
        model,
        api_key,
        base_url,
        provider,
    ) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai not installed. Run: pip install openai")

        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = OpenAI(**client_kwargs)
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

        if json_mode and content is not None:
            content = self._strip_markdown_fences(content)

        return LLMResponse(
            content=content,
            model=chosen_model,
            provider=provider,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            raw=response,
        )
