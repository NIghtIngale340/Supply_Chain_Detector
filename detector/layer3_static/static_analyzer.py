from typing import Any
import re
from detector.layer3_static.ast_analyzer import analyze_ast 
from detector.layer3_static.semgrep_runner import run_semgrep 
from detector.layer3_static.obfuscation_detector import analyze_obfuscation 




_COMPONENT_WEIGHTS: dict[str, float] = {
    "ast": 0.40, "semgrep": 0.35, "obfuscation": 0.25,
}
_THRESHOLD_REVIEW    = 30
_THRESHOLD_HIGH_RISK = 70


_HIGH_SIGNAL_PATTERNS: list[tuple[str, int, str]] = [
    (r"\bexec\s*\(", 20, "dynamic exec"),
    (r"\beval\s*\(", 20, "dynamic eval"),
    (r"base64\.b64decode\s*\(", 10, "base64 decode"),
    (r"socket\.socket\s*\(", 12, "socket usage"),
    (r"\.connect\s*\(", 12, "outbound connect"),
    (r"subprocess\.(?:call|Popen|run|check_output)\s*\(", 14, "subprocess execution"),
    (r"os\.system\s*\(", 14, "shell execution"),
    (r"\bos\.environ\b", 8, "environment access"),
    (r"__import__\s*\(", 8, "dynamic import"),
    (r"open\s*\(\s*['\"]\/tmp\/", 8, "writes to /tmp"),
]


def _score_high_signal_patterns(source_code: str) -> tuple[int, list[str], set[str]]:
    raw_score = 0
    evidence: list[str] = []
    hits: set[str] = set()

    for pattern, points, label in _HIGH_SIGNAL_PATTERNS:
        if re.search(pattern, source_code, flags=re.IGNORECASE):
            raw_score += points
            hits.add(label)
            evidence.append(f"[Pattern] {label} (+{points})")

    if "dynamic exec" in hits and "base64 decode" in hits:
        raw_score += 10
        evidence.append("[Pattern] encoded payload execution (base64 + exec) (+10)")

    if "socket usage" in hits and "outbound connect" in hits:
        raw_score += 8
        evidence.append("[Pattern] active network beacon behavior (+8)")

    if "writes to /tmp" in hits and "dynamic import" in hits:
        raw_score += 8
        evidence.append("[Pattern] dropper behavior (/tmp write + dynamic import) (+8)")

    return min(100, max(0, raw_score)), evidence, hits


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
    pattern_score, pattern_evidence, pattern_hits = _score_high_signal_patterns(source_code)
    component_scores = {
        "ast": ast_result.get("risk_score", 0),
        "semgrep": semgrep_result.get("risk_score", 0),
        "obfuscation": obfuscation_result.get("risk_score", 0),
        "high_signal_patterns": pattern_score,
    }
    weighted_component_score = sum(
        component_scores[comp] * _COMPONENT_WEIGHTS[comp]
        for comp in _COMPONENT_WEIGHTS
    )
    final_score = round(min(max(max(weighted_component_score, pattern_score), 0), 100))
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
    combined_evidence.extend(pattern_evidence)
    return {
        "final_score": final_score,
        "decision": decision,
        "component_scores": component_scores,
        "pattern_hits": sorted(pattern_hits),
        "evidence": combined_evidence,
    }
