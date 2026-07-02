"""
Plan configuration — maps subscription plans to allowed LLM providers/models
and monthly quota limits.

Plans:
  free        — only free models (Z.AI flash, OpenCode free tier)
  premium     — free + mid-cost models (GPT-4o-mini, Claude Haiku, GLM-4.5)
  enterprise  — all models, no restrictions
"""

from typing import Dict, List, Set

# ── Model access per plan ────────────────────────────────────────────────────

PLAN_MODELS: Dict[str, Dict[str, List[str]]] = {
    "free": {
        "zai": [
            "glm-4.5-flash",
            "glm-4.7-flash",
        ],
        "opencode": [
            "opencode/deepseek-v4-flash-free",
            "opencode/mimo-v2.5-free",
            "opencode/north-mini-code-free",
            "opencode/nemotron-3-ultra-free",
            "opencode/nemotron-3-super-free",
            "opencode/big-pickle",
        ],
        "openai": [],
        "anthropic": [],
    },
    "premium": {
        "zai": [
            "glm-4.5-flash",
            "glm-4.7-flash",
            "glm-4.5",
            "glm-4.5-air",
            "glm-4.6",
        ],
        "opencode": [
            "opencode/deepseek-v4-flash-free",
            "opencode/mimo-v2.5-free",
            "opencode/north-mini-code-free",
            "opencode/nemotron-3-ultra-free",
            "opencode/nemotron-3-super-free",
            "opencode/big-pickle",
            "opencode/qwen3.5-plus",
            "opencode/qwen3.6-plus",
            "opencode/gemini-3.5-flash",
            "opencode/glm-5",
            "opencode/kimi-k2.5",
        ],
        "openai": [
            "gpt-4o-mini",
        ],
        "anthropic": [
            "claude-haiku-4-5",
        ],
    },
    "enterprise": {
        "zai": [
            "glm-4.5-flash",
            "glm-4.7-flash",
            "glm-4.5",
            "glm-4.5-air",
            "glm-4.6",
            "glm-4.7",
            "glm-5",
            "glm-5.1",
        ],
        "opencode": [
            "opencode/deepseek-v4-flash-free",
            "opencode/mimo-v2.5-free",
            "opencode/north-mini-code-free",
            "opencode/nemotron-3-ultra-free",
            "opencode/nemotron-3-super-free",
            "opencode/big-pickle",
            "opencode/qwen3.5-plus",
            "opencode/qwen3.6-plus",
            "opencode/gpt-5.5",
            "opencode/gpt-5.5-pro",
            "opencode/claude-opus-4-5",
            "opencode/claude-sonnet-4-5",
            "opencode/gemini-3.5-flash",
            "opencode/glm-5",
            "opencode/kimi-k2.5",
            "opencode/grok-build-0.1",
        ],
        "openai": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
        ],
        "anthropic": [
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
        ],
    },
}

# ── Monthly quota (LLM requests) per plan ────────────────────────────────────

PLAN_QUOTAS: Dict[str, int] = {
    "free": 100,
    "premium": 2000,
    "enterprise": 10000,
}

# ── Plan labels for frontend display ─────────────────────────────────────────

PLAN_LABELS: Dict[str, str] = {
    "free": "Free",
    "premium": "Premium",
    "enterprise": "Enterprise",
}

# ── Default provider preference per plan (for auto mode) ─────────────────────

PLAN_DEFAULT_PROVIDER: Dict[str, str] = {
    "free": "zai",
    "premium": "opencode",
    "enterprise": "anthropic",
}


def get_allowed_models(plan: str, provider: str) -> List[str]:
    """Returns the list of model IDs allowed for a given plan and provider."""
    return PLAN_MODELS.get(plan, PLAN_MODELS["free"]).get(provider, [])


def is_model_allowed(plan: str, provider: str, model_id: str) -> bool:
    """Checks if a specific model is allowed for the user's plan."""
    allowed = get_allowed_models(plan, provider)
    return model_id in allowed


def get_quota(plan: str) -> int:
    """Returns the monthly LLM request quota for a plan."""
    return PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])


def get_default_provider(plan: str) -> str:
    """Returns the preferred provider for auto-mode given the plan."""
    return PLAN_DEFAULT_PROVIDER.get(plan, "auto")


def get_available_providers(plan: str) -> List[str]:
    """Returns providers that have at least one allowed model for the plan."""
    plan_models = PLAN_MODELS.get(plan, PLAN_MODELS["free"])
    return [p for p, models in plan_models.items() if models]
