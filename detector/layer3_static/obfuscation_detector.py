import re
from typing import Any

_MIN_BASE64_LEN = 200

_SIGNAL_WEIGHTS: dict[str, int] = {
    "long_base64": 20, "hex_encoded": 15, "eval_compile": 30,
    "lambda_heavy": 10, "write_then_import": 15,
}


def _detect_base64_blobs(source: str) -> list[str]:
    pattern = r"""['\"]([A-Za-z0-9+/=]{200,})['\"]"""
    matches = re.findall(pattern, source)
    evidence, seen = [], set()
    for match in matches:
        preview = match[:50] + "..."
        if preview not in seen:
            seen.add(preview)
            evidence.append(f"Base64-like string ({len(match)} chars): {preview}")
    return evidence


def _detect_hex_strings(source: str) -> list[str]:
    pattern = r"""(?:\\x[0-9a-fA-F]{2}){10,}"""
    matches = re.findall(pattern, source)
    evidence = []
    for match in matches:
        evidence.append(
            f"Hex-encoded sequence ({len(match)} chars): {match[:60]}..."
        )
    return evidence


def _detect_eval_compile(source: str) -> list[str]:
    pattern = r"\b(?:eval\s*\(\s*compile\s*\(|exec\s*\(\s*compile\s*\()"
    matches = re.findall(pattern, source)
    evidence = []
    for match in matches:
        evidence.append(f"eval/exec(compile()) chain detected: {match.strip()}")
    return evidence


def _detect_lambda_heavy(source: str) -> list[str]:
    matches = re.findall(r"\blambda\b", source)
    if len(matches) > 10:
        return [f"High lambda count: {len(matches)} lambdas"]
    return []


def _detect_write_then_import(source: str) -> list[str]:
    write_pattern = r"""open\s*\([^)]*\.py['\"].*['\"]w['\"]"""
    import_pattern = r"\b(?:importlib\s*\(|__import__\s*\()"
    if re.search(write_pattern, source) and re.search(import_pattern, source):
        return ["Write-then-import: file written then dynamically imported"]
    return []


def analyze_obfuscation(source_code: str) -> dict[str, Any]:
    if not source_code or not source_code.strip():
        return {
            "risk_score": 0,
            "signals": [],
            "is_suspicious": False,
            "evidence": ["Empty source code provided"],
        }
    all_signals: list[str] = []
    signal_hits: dict[str, bool] = {}
    detectors = {
        "long_base64":       _detect_base64_blobs,
        "hex_encoded":       _detect_hex_strings,
        "eval_compile":      _detect_eval_compile,
        "lambda_heavy":      _detect_lambda_heavy,
        "write_then_import": _detect_write_then_import,
    }
    evidence: list[str] = []
    for signal_name, detector_fn in detectors.items():
        results = detector_fn(source_code)
        if results:
            signal_hits[signal_name] = True
            all_signals.append(signal_name)
            evidence.extend(results)
    risk_score = sum(
        _SIGNAL_WEIGHTS[sig]
        for sig in signal_hits if signal_hits[sig]
    )
    return {
        "risk_score": risk_score,
        "signals": all_signals,
        "is_suspicious": risk_score >= 25,
        "evidence": evidence,
    }