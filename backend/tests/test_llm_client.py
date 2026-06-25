"""
Testes para o LLMClient unificado.
"""

import pytest

from core.llm_client import LLMClient


def _clear_llm_keys(monkeypatch):
    """Remove todas as chaves de LLM para testes isolados."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENCODE_API_KEY", raising=False)
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)


def test_opencode_auto_selected(monkeypatch):
    """Quando só OPENCODE_API_KEY está definida, o provider deve ser opencode."""
    _clear_llm_keys(monkeypatch)
    monkeypatch.setenv("OPENCODE_API_KEY", "sk-test-opencode")

    client = LLMClient()
    assert client.provider == "opencode"
    assert client.default_model == "opencode/deepseek-v4-flash-free"
    assert client.smart_model == "opencode/big-pickle"


def test_opencode_forced_preference(monkeypatch):
    """LLM_PROVIDER=opencode força o provider mesmo com outras chaves presentes."""
    _clear_llm_keys(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("OPENCODE_API_KEY", "sk-test-opencode")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    client = LLMClient()
    assert client.provider == "opencode"


def test_no_provider_raises(monkeypatch):
    """Sem nenhuma chave configurada, LLMClient deve levantar RuntimeError."""
    _clear_llm_keys(monkeypatch)
    with pytest.raises(RuntimeError):
        LLMClient()


def test_zai_auto_selected(monkeypatch):
    """Quando só ZAI_API_KEY está definida, o provider deve ser zai."""
    _clear_llm_keys(monkeypatch)
    monkeypatch.setenv("ZAI_API_KEY", "161c...d3f87.zo6...")

    client = LLMClient()
    assert client.provider == "zai"
    assert client.default_model == "glm-4.5-flash"
    assert client.smart_model == "glm-4.5"


def test_zai_forced_preference(monkeypatch):
    """LLM_PROVIDER=zai força o provider mesmo com outras chaves presentes."""
    _clear_llm_keys(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("ZAI_API_KEY", "161c...d3f87.zo6...")
    monkeypatch.setenv("LLM_PROVIDER", "zai")

    client = LLMClient()
    assert client.provider == "zai"


def test_model_override(monkeypatch):
    """O model override deve ser respeitado para qualquer provider."""
    _clear_llm_keys(monkeypatch)
    monkeypatch.setenv("OPENCODE_API_KEY", "sk-test-opencode")

    client = LLMClient(model_override="opencode/qwen3.5-plus")
    assert client.default_model == "opencode/qwen3.5-plus"
    assert client.smart_model == "opencode/qwen3.5-plus"
