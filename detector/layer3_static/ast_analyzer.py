import ast
import re
from typing import Any

_DANGEROUS_CALLS: dict[str, list[str]] = {
    "subprocess": ["call", "run", "Popen", "check_output"],
    "socket":     ["socket", "connect"],
    "eval_exec":  ["eval", "exec"],
    "os_environ":  ["os.environ"],
    "file_ops":   ["open", "read", "write"],
    "base64":     ["b64decode", "decodebytes"],
}

_RISK_WEIGHTS: dict[str, int] = {
    "subprocess": 15,
    "socket":     15,
    "eval_exec":  20,
    "os_environ":  10,
    "file_ops":   5,
    "base64":     15,
}


class _DangerousCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.counts: dict[str, int] = {k: 0 for k in _DANGEROUS_CALLS}
        self.evidence: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._extract_name(node)
        if func_name:
            self._check_match(func_name, node.lineno)
        self.generic_visit(node)

    def _extract_name(self, node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _check_match(self, name: str, lineno: int) -> None:
        for category, patterns in _DANGEROUS_CALLS.items():
            for pattern in patterns:
                if pattern.lower() in name.lower():
                    self.counts[category] += 1
                    self.evidence.append(
                        f"Line {lineno}: {category} — '{name}' matches '{pattern}'"
                    )


def _regex_fallback(source_code: str) -> tuple[dict[str, int], list[str]]:
    counts = {k: 0 for k in _DANGEROUS_CALLS}
    evidence: list[str] = []
    _FALLBACK_PATTERNS = {
        "subprocess": r"\b(?:subprocess\.(?:call|run|Popen)|check_output)\b",
        "socket":     r"\b(?:socket\.socket|\.connect\()\b",
        "eval_exec":  r"\b(?:eval\(|exec\()",
        "os_environ":  r"\bos\.environ\b",
        "file_ops":   r"\bopen\s*\(",
        "base64":     r"\bbase64\.b64decode\b",
    }
    for category, pattern in _FALLBACK_PATTERNS.items():
        matches = re.findall(pattern, source_code)
        count = len(matches)
        counts[category] = count
        if count > 0:
            evidence.append(f"Regex fallback: {count} '{category}' match(es)")
    return counts, evidence


def analyze_ast(source_code: str) -> dict[str, Any]:
    if not source_code or not source_code.strip():
        return {
            "risk_score": 0,
            "feature_vector": {k: 0 for k in _DANGEROUS_CALLS},
            "is_suspicious": False,
            "evidence": ["Empty source code provided"],
        }
    try:
        tree = ast.parse(source_code)
        visitor = _DangerousCallVisitor()
        visitor.visit(tree)
        counts = visitor.counts
        evidence = visitor.evidence
    except SyntaxError as e:
        evidence_header = f"AST parse failed ({e.__class__.__name__}), using regex fallback"
        counts, regex_evidence = _regex_fallback(source_code)
        evidence = [evidence_header] + regex_evidence

    raw_score = sum(counts[cat] * _RISK_WEIGHTS[cat] for cat in counts)
    risk_score = min(100, max(0, raw_score))

    return {
        "risk_score": risk_score,
        "feature_vector": counts,
        "is_suspicious": risk_score >= 30,
        "evidence": evidence,
    }
