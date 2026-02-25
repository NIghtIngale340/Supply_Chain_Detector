from datetime import datetime, timezone

def _parse_iso_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def analyze_author_signals(metadata: dict, registry: str) -> dict:
    author = metadata.get("author", "")
    created_at_str = metadata.get("created_at", None)

    if not author and registry == "npm":
        author_obj = metadata.get("author", {})
        if isinstance(author_obj, dict):
            author = author_obj.get("name", "")

    account_age_days = None
    created_at = _parse_iso_date(created_at_str)
    if created_at is not None:
        now = datetime.now(tz=timezone.utc)
        delta = now - created_at
        account_age_days = delta.days

    published_count = metadata.get("published_count", None)

    if published_count is not None and published_count >= 10:
        reputation = "high"
    elif published_count is not None and published_count >= 3:
        reputation = "medium"
    else:
        reputation = "low"

    risk_score = 0
    evidence = []

    if account_age_days is not None and account_age_days < 30:
        risk_score += 30
        evidence.append(f"Account is only {account_age_days} days old (< 30 days)")

    if account_age_days is not None and account_age_days < 7:
        risk_score += 20
        evidence.append(f"Account is very new: {account_age_days} days old (< 7 days)")

    if not author:
        risk_score += 10
        evidence.append("No author information available")

    if reputation == "low":
        risk_score += 15
        evidence.append(f"Author reputation is low (published count: {published_count})")

    risk_score = max(0, min(100, risk_score))

    is_suspicious = risk_score >= 40

    if not evidence:
        evidence.append("No risk signals detected")

    return {
        "risk_score": risk_score, "account_age_days": account_age_days,
        "published_package_count": published_count, "maintainer_reputation": reputation,
        "is_suspicious": is_suspicious, "evidence": evidence,
    }
