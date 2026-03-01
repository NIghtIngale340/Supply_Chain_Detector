from typing import Any
from detector.layer3_static.ast_analyzer import analyze_ast 
from detector.layer3_static.semgrep_runner import run_semgrep 
from detector.layer3_static.obfuscation_detector import analyze_obfuscation 




_COMPONENT_WEIGHTS: dict[str, float] = {
    "ast": 0.40, "semgrep": 0.35, "obfuscation": 0.25,
}
_THRESHOLD_REVIEW    = 30
_THRESHOLD_HIGH_RISK = 70


def _run_component(name: str, func, *args) -> dict:
    try:
        return func(*args)
    except Exception as e:
        return {"risk_score": 0, "is_suspicious": False, "evidence": [f"{name} failed: {e}"]}


def analyze_static_risk(source_code: str, source_path: str | None = None) -> dict[str, Any]:
    if not source_code or not source_code.strip():
        return {"final_score": 0, "decision": "allow",
                "component_scores": {"ast": 0, "semgrep": 0, "obfuscation": 0},
                "evidence": ["No source code provided"]}
    ast_result = _run_component("ast_analyzer", analyze_ast, source_code)
    if source_path:
        semgrep_result = _run_component("semgrep_runner", run_semgrep, source_path)
    else:
        semgrep_result = {"risk_score": 0, "is_suspicious": False,
                          "evidence": ["No source path — Semgrep skipped"]}
    obfuscation_result = _run_component("obfuscation_detector", analyze_obfuscation, source_code)
    component_scores = {
        "ast": ast_result.get("risk_score", 0),
        "semgrep": semgrep_result.get("risk_score", 0),
        "obfuscation": obfuscation_result.get("risk_score", 0),
    }
    final_score = sum(component_scores[comp] * _COMPONENT_WEIGHTS[comp] for comp in _COMPONENT_WEIGHTS)
    final_score = round(min(max(final_score, 0), 100))
    if final_score >= _THRESHOLD_HIGH_RISK:
        decision = "high_risk"
    elif final_score >= _THRESHOLD_REVIEW:
        decision = "review"
    else:
        decision = "allow"
    combined_evidence: list[str] = []
    for name, result in [("AST", ast_result), ("Semgrep", semgrep_result), ("Obfuscation", obfuscation_result)]:
        for item in result.get("evidence", []):
            combined_evidence.append(f"[{name}] {item}")
    return {
        "final_score": final_score,
        "decision": decision,
        "component_scores": component_scores,
        "evidence": combined_evidence,
    }