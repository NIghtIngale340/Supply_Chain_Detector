import os
from typing import Any

import requests

from detector.layer4_llm.deobfuscator import deobfuscate_source
from detector.layer4_llm.response_parser import parse_llm_audit_response
from detector.layer4_llm.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def _stub_llm_inference(_system_prompt: str, _user_prompt: str) -> str:
    return '{"risk_score": 0, "risk_category": "benign", "summary": "Stubbed LLM response.", "evidence": ["LLM provider is set to stub"]}'


def _openai_inference(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "600"))
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI LLM provider")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"]


def _nvidia_inference(system_prompt: str, user_prompt: str) -> str:
    api_key = os.getenv("NVIDIA_API_KEY", "")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
    max_tokens = int(os.getenv("NVIDIA_MAX_OUTPUT_TOKENS", "600"))
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is required for NVIDIA NIM LLM provider")

    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"]


def _ollama_inference(system_prompt: str, user_prompt: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "huihui_ai/qwen2.5-coder-abliterate:7b")
    max_tokens = int(os.getenv("OLLAMA_MAX_OUTPUT_TOKENS", "600"))
    response = requests.post(
        f"{base_url.rstrip('/')}/api/generate",
        json={
            "model": model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": max_tokens,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    return str(payload.get("response", ""))


def _invoke_llm(system_prompt: str, user_prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "disabled").lower()
    if provider in {"", "disabled", "off", "none"}:
        raise RuntimeError("LLM provider is disabled")
    if provider == "openai":
        return _openai_inference(system_prompt, user_prompt)
    if provider == "nvidia":
        return _nvidia_inference(system_prompt, user_prompt)
    if provider == "ollama":
        return _ollama_inference(system_prompt, user_prompt)
    if provider == "stub":
        return _stub_llm_inference(system_prompt, user_prompt)
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")


def audit_code_with_llm(source_code: str, prior_layer_score: int, trigger_threshold: int = 40) -> dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "disabled").lower()

    if prior_layer_score < trigger_threshold:
        return {
            "llm_triggered": False,
            "trigger_threshold": trigger_threshold,
            "provider": provider,
            "reason": f"Prior risk ({prior_layer_score}) below threshold ({trigger_threshold}).",
            "risk_score": 0,
            "audit_result": None,
        }

    deobfuscation_result = deobfuscate_source(source_code)
    cleaned_source = deobfuscation_result["cleaned_source"]

    user_prompt = USER_PROMPT_TEMPLATE.format(source_code=cleaned_source)

    try:
        raw_llm_output = _invoke_llm(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        return {
            "llm_triggered": True,
            "trigger_threshold": trigger_threshold,
            "provider": provider,
            "reason": f"LLM API failure: {e}",
            "risk_score": 0,
            "audit_result": None,
        }

    audit_data = parse_llm_audit_response(raw_llm_output)

    return {
        "llm_triggered": True,
        "trigger_threshold": trigger_threshold,
        "provider": provider,
        "reason": "Prior-layer risk exceeded threshold. Audit completed.",
        "risk_score": int(audit_data.get("risk_score", 0)),
        "audit_result": audit_data,
        "preprocessing_warnings": deobfuscation_result.get("warnings", []),
        "preprocessing_transformations": deobfuscation_result.get("transformations_applied", []),
    }

