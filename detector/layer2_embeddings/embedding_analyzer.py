from detector.layer2_embeddings.code_embedder import encode as embed_code
from detector.layer2_embeddings.cluster_manager import find_nearest

# Thresholds calibrated to real FAISS index L2 distances
# Benign code typically has L2 distance 0.5-1.2 from nearest benign cluster
# Suspicious code: 1.2-1.8, Malicious/novel code: >1.8
DISTANCE_THRESHOLDS = {"safe": 0.8, "moderate": 1.6}


def embedding_risk_score(distance):
    if distance <= DISTANCE_THRESHOLDS["safe"]:
        return 0
    elif distance <= DISTANCE_THRESHOLDS["moderate"]:
        safe = DISTANCE_THRESHOLDS["safe"]
        moderate = DISTANCE_THRESHOLDS["moderate"]
        ratio = (distance - safe) / (moderate - safe)
        return int(20 + ratio * 40)
    else:
        return min(95, int(60 + (distance - DISTANCE_THRESHOLDS["moderate"]) * 25))


def analyze_embedding_risk(source_code):
    try:
        embedding = embed_code(source_code)
    except Exception as e:
        return {"risk_score": 0, "distance": None, "nearest_neighbors": [], "is_suspicious": False, "evidence": [f"Embedding failed: {e}"]}

    try:
        neighbors = find_nearest(embedding, k=5)
        distance = neighbors[0]["distance"] if neighbors else float("inf")
    except FileNotFoundError as e:
        return {"risk_score": 0, "distance": None, "nearest_neighbors": [], "is_suspicious": False, "evidence": [f"FAISS index unavailable: {e}"]}

    risk = embedding_risk_score(distance)
    is_suspicious = risk >= 40
    evidence = []
    if is_suspicious:
        evidence.append(f"Code embedding is distant from benign clusters (L2={distance:.2f}, risk={risk})")
    else:
        nearest_name = neighbors[0]["name"] if neighbors else "unknown"
        evidence.append(f"Code embedding is close to benign package '{nearest_name}' (L2={distance:.2f})")

    return {"risk_score": risk, "distance": round(distance, 4), "nearest_neighbors": neighbors[:3], "is_suspicious": is_suspicious, "evidence": evidence}
