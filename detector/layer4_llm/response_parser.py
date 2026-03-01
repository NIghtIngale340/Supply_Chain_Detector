import json
import re
from typing import Any


def _get_fallback_response(error_message: str) -> dict[str, Any]:
    return {
        "risk_score": 100,
        "risk_category": "suspicious",
        "summary": "LLM failed to produce a valid structured response.",
        "evidence": [error_message],
    }


def parse_llm_audit_response(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()

    # Strip opening markdown fence (```json or ```)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
    # Strip closing markdown fence
    text = re.sub(r"\n?```\s*$", "", text)

    # Snap to the first { and last } in case LLM added preamble/postamble text
    start_idx = text.find("{")
    end_idx = text.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        text = text[start_idx:end_idx + 1]

    try:
        parsed_json = json.loads(text)

        raw_risk_score = int(parsed_json.get("risk_score", 0))
        risk_score = max(0, min(100, raw_risk_score))
        risk_category = str(parsed_json.get("risk_category", "unknown")).lower()
        if risk_category not in {"benign", "suspicious", "malicious"}:
            risk_category = "unknown"

        evidence = parsed_json.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = [str(evidence)]
        evidence = [str(item) for item in evidence][:20]

        strict_response = {
            "risk_score": risk_score,
            "risk_category": risk_category,
            "summary": str(parsed_json.get("summary", "")),
            "evidence": evidence,
        }
        return strict_response

    except json.JSONDecodeError as e:
        return _get_fallback_response(f"JSON Decode Error: {e}")
    except (ValueError, TypeError) as e:
        return _get_fallback_response(f"Type Coercion Error: {e}")
