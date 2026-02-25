from detector.layer1_metadata.typosquat_detector import analyze_typosquat
from detector.layer1_metadata.author_analyzer import analyze_author_signals
from detector.layer1_metadata.version_analyzer import analyze_version_signals


WEIGHTS = {
    "typosquat": 0.40,
    "author":    0.30,
    "version":   0.30,
}

THRESHOLDS = {  
    "high_risk": 70,
    "review":    40,
}


def _safe_call(func, *args, **kwargs) -> dict:
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return {"risk_score": 0.0, "is_suspicious": False, "evidence": [f"Analyzer error: {str(e)}"]}


def analyze_metadata_risk(package_name: str, registry: str, metadata: dict) -> dict:
    typosquat_result = _safe_call(analyze_typosquat, package_name, registry)
    author_result = _safe_call(analyze_author_signals, metadata, registry)
    version_result = _safe_call(analyze_version_signals, metadata)

    typo_score = typosquat_result.get("risk_score", 0.0)
    auth_score = author_result.get("risk_score", 0.0)
    ver_score = version_result.get("risk_score", 0.0)

    final_score = (
        typo_score * WEIGHTS["typosquat"]
        + auth_score * WEIGHTS["author"]
        + ver_score * WEIGHTS["version"]
    )
    final_score = max(0, min(100, final_score))

    if final_score >= THRESHOLDS["high_risk"]:
        decision = "high_risk"
    elif final_score >= THRESHOLDS["review"]:
        decision = "review"
    else:
        decision = "allow"

    combined_evidence = (
        typosquat_result.get("evidence", [])
        + author_result.get("evidence", [])
        + version_result.get("evidence", [])
    )

    return {
        "final_score": final_score, "decision": decision,
        "layer_scores": {"typosquat": typo_score, "author": auth_score, "version": ver_score},
        "thresholds": THRESHOLDS, "evidence": combined_evidence,
    }
