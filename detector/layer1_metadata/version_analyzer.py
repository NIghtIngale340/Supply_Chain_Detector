import re
from datetime import datetime, timezone
from typing import Optional, Tuple

def _parse_version(version_str: str) -> Optional[Tuple[int, ...]]:
    if not version_str:
        return None
    parts = re.findall(r"\d+", version_str)
    if not parts:
        return None
    return tuple(int(p) for p in parts)


def _version_jump_magnitude(old: Tuple[int, ...], new: Tuple[int, ...]) -> float:
    max_len = max(len(old), len(new))
    old_padded = old + (0,) * (max_len - len(old))
    new_padded = new + (0,) * (max_len - len(new))
    total_diff = sum(abs(a - b) for a, b in zip(new_padded, old_padded))
    return float(total_diff)


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

def analyze_version_signals(metadata: dict) -> dict:
    current_version_str = metadata.get("version", "")
    release_history = metadata.get("release_history", [])
    _parse_version(current_version_str)

    version_jump = None
    release_velocity = None
    days_since_last = None
    risk_score = 0
    evidence = []

    dated_releases = []
    for release in release_history:
        date = _parse_iso_date(release.get("date"))
        ver = _parse_version(release.get("version"))
        if date is not None:
            dated_releases.append({"date": date, "version": ver, "raw": release})
    dated_releases.sort(key=lambda r: r["date"])

    if len(dated_releases) >= 2:
        latest = dated_releases[-1]
        previous = dated_releases[-2]

        if latest["version"] and previous["version"]:
            version_jump = _version_jump_magnitude(previous["version"], latest["version"])

        now = datetime.now(tz=timezone.utc)
        delta = now - latest["date"]
        days_since_last = delta.days

        gap = latest["date"] - previous["date"]
        gap_days = max(gap.days, 1)
        if version_jump is not None:
            release_velocity = round(version_jump / gap_days, 4)

    if version_jump is not None and version_jump > 5:
        risk_score += 30
        evidence.append(f"Large version jump detected: magnitude {version_jump}")

    if days_since_last is not None and len(dated_releases) >= 2:
        prev_gap = (dated_releases[-1]["date"] - dated_releases[-2]["date"]).days
        if prev_gap > 365:
            risk_score += 35
            evidence.append(f"Package was dormant for {prev_gap} days before latest release")

    if len(dated_releases) < 2:
        risk_score += 10
        evidence.append("Insufficient release history for analysis")

    if release_velocity is not None and release_velocity > 1.0:
        risk_score += 15
        evidence.append(f"High release velocity: {release_velocity} magnitude/day")

    risk_score = max(0, min(100, risk_score))
    is_suspicious = risk_score >= 30

    if not evidence:
        evidence.append("No version anomalies detected")

    return {
        "risk_score": risk_score, "version_jump_magnitude": version_jump,
        "release_velocity": release_velocity, "days_since_last_release": days_since_last,
        "is_suspicious": is_suspicious, "evidence": evidence,
    }
