import json
from pathlib import Path


def _levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


_THIS_DIR = Path(__file__).parent.resolve()
_PROJECT_ROOT = _THIS_DIR.parent.parent

_TOP_PACKAGE_FILES = {
    "pypi": _PROJECT_ROOT / "data" / "top_packages" / "pypi_top_1000.json",
    "npm":  _PROJECT_ROOT / "data" / "top_packages" / "npm_top_1000.json",
}


def _load_top_packages(registry: str) -> list[str]:
    file_path = _TOP_PACKAGE_FILES.get(registry)
    if file_path is None:
        return ["No package list available for registry"]
    if not file_path.exists():
        return ["File path doesnt  exist"]
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_typosquat(package_name: str, registry: str) -> dict:
    name = package_name.lower().strip()

    if not name:
        return {
            "risk_score": 0, "nearest_package": None, "edit_distance": None,
            "is_suspicious": False, "evidence": ["Empty package name provided"],
        }

    top_packages = _load_top_packages(registry)
    if not top_packages:
        return {
            "risk_score": 0, "nearest_package": None, "edit_distance": None,
            "is_suspicious": False,
            "evidence": [f"No top package list available for registry: {registry}"],
        }

    best_distance = float("inf")
    best_match = None

    for pkg in top_packages:
        dist = _levenshtein(name, pkg.lower())
        if dist < best_distance:
            best_distance = dist
            best_match = pkg

    if best_distance == 0:
        return {
            "risk_score": 0, "nearest_package": best_match, "edit_distance": 0,
            "is_suspicious": False, "evidence": [f"Package '{name}' is a known popular package"],
        }

    if best_distance == 1:
        risk_score = 90
    elif best_distance == 2:
        risk_score = 60
    elif best_distance <= 4:
        risk_score = 25
    else:
        risk_score = 0

    is_suspicious = best_distance <= 2

    evidence = []
    if is_suspicious:
        evidence.append(f"Package '{name}' is {best_distance} edit(s) away from popular package '{best_match}'")
    else:
        evidence.append(f"Package '{name}' is not close to any popular {registry} package (nearest: '{best_match}', distance: {best_distance})")

    return {
        "risk_score": risk_score, "nearest_package": best_match, "edit_distance": best_distance,
        "is_suspicious": is_suspicious, "evidence": evidence,
    }
