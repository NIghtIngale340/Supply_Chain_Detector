from typing import Any

from detector.layer4_llm.deobfuscator import deobfuscate_source
from detector.layer4_llm.response_parser import parse_llm_audit_response
from detector.layer4_llm.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

_LLM_TRIGGER_THRESHOLD = 40


def stub_llm_inference(system_prompt: str, user_prompt: str) -> str:
    return '{"risk_score": 99, "risk_category": "malicious", "summary": "Mock", "evidence": []}'


def audit_code_with_llm(source_code: str, prior_layer_score: int) -> dict[str, Any]:
    if prior_layer_score < _LLM_TRIGGER_THRESHOLD:
        return {
            "llm_triggered": False,
            "trigger_threshold": _LLM_TRIGGER_THRESHOLD,
            "reason": f"Prior risk ({prior_layer_score}) below threshold ({_LLM_TRIGGER_THRESHOLD}).",
            "audit_result": None,
        }

    deobfuscation_result = deobfuscate_source(source_code)
    cleaned_source = deobfuscation_result["cleaned_source"]

    user_prompt = USER_PROMPT_TEMPLATE.format(source_code=cleaned_source)

    try:
        raw_llm_output = stub_llm_inference(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        return {
            "llm_triggered": True,
            "trigger_threshold": _LLM_TRIGGER_THRESHOLD,
            "reason": f"LLM API failure: {e}",
            "audit_result": None,
        }

    audit_data = parse_llm_audit_response(raw_llm_output)

    return {
        "llm_triggered": True,
        "trigger_threshold": _LLM_TRIGGER_THRESHOLD,
        "reason": "Prior-layer risk exceeded threshold. Audit completed.",
        "audit_result": audit_data,
        "preprocessing_warnings": deobfuscation_result.get("warnings", []),
        "preprocessing_transformations": deobfuscation_result.get("transformations_applied", []),
    }
