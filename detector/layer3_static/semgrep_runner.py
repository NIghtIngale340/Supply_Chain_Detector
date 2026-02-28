import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
_DEFAULT_RULES_DIR = _PROJECT_ROOT / "data" / "semgrep_rules"

_SEVERITY_WEIGHTS: dict[str, int] = {
    "ERROR": 25, "WARNING": 15, "INFO": 5,
}


def _semgrep_available() -> bool:
    return shutil.which("semgrep") is not None


def _run_semgrep_process(target_path: str, rules_dir: str) -> dict:
    cmd = [
        "semgrep", "--config", rules_dir, "--json",
        "--no-git-ignore", "--quiet", target_path,
    ]
    result = subprocess.run(cmd, capture_output=True, encoding="utf-8", timeout=60)
    if result.returncode not in (0, 1):
        return {"error": f"Semgrep failed (exit {result.returncode}): {result.stderr}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse Semgrep JSON output"}


def _normalize_findings(raw_output: dict) -> list[dict]:
    findings = []
    for result in raw_output.get("results", []):
        finding = {
            "rule_id":  result.get("check_id", "unknown"),
            "severity": result.get("extra", {}).get("severity", "INFO"),
            "message":  result.get("extra", {}).get("message", ""),
            "path":     result.get("path", ""),
            "line":     result.get("start", {}).get("line", result.get("line", 0)),
            "matched":  result.get("extra", {}).get("lines", ""),
        }
        findings.append(finding)
    return findings


def run_semgrep(target_path: str, rules_dir: str | None = None) -> dict[str, Any]:
    rules = rules_dir or str(_DEFAULT_RULES_DIR)
    if not _semgrep_available():
        return {"risk_score": 0, "finding_count": 0, "findings": [],
                "is_suspicious": False, "evidence": ["Semgrep binary not found"]}
    if not Path(target_path).exists():
        return {"risk_score": 0, "finding_count": 0, "findings": [],
                "is_suspicious": False, "evidence": [f"Target path missing: {target_path}"]}
    raw = _run_semgrep_process(target_path, rules)
    if "error" in raw:
        return {"risk_score": 0, "finding_count": 0, "findings": [],
                "is_suspicious": False, "evidence": [raw["error"]]}
    findings = _normalize_findings(raw)
    risk_score = sum(_SEVERITY_WEIGHTS.get(f["severity"], 5) for f in findings)
    risk_score = min(risk_score, 100)
    evidence = [f"{f['rule_id']} ({f['severity']}) at {f['path']}:{f['line']}" for f in findings]
    return {
        "risk_score": risk_score,
        "finding_count": len(findings),
        "findings": findings,
        "is_suspicious": risk_score >= 25,
        "evidence": evidence,
    }
