"""Explainable niche, micro-tier, engagement, and channel-type filtering."""
from __future__ import annotations
import re


def classify(row: dict) -> tuple[bool, str]:
    reasons = []
    titles = [t.strip() for t in row.get("content_themes", "").split(" | ") if t.strip() and t.strip() != "Not Available"]
    relevant = re.compile(r"fit|workout|yoga|gym|train|run|nutrition|health|exercise|asana|pose|strength|muscle|weight\s?loss|mma|martial\s?arts|diet|creatine|bodybuild|mobility|stretch", re.I)
    if row.get("niche") != "Fitness" or sum(bool(relevant.search(t)) for t in titles) < 2:
        reasons.append("content relevance: fewer than two recent public video titles clearly match fitness")
    name = row.get("name", "")
    if re.search(r"\s-\sTopic$", name, re.I): reasons.append("not an individual creator channel (YouTube Topic channel)")
    if re.search(r"\b(association|federation|institute|school|sansthan)\b", name, re.I):
        reasons.append("organization or institution channel, not an individual creator")
    country = row.get("channel_country")
    if country not in (None, "", "Not Available", "IN"):
        reasons.append(f"channel country is {country}, outside India focus")
    try: followers = int(row.get("followers", 0))
    except (ValueError, TypeError): followers = 0
    if not 5000 <= followers <= 100000: reasons.append("follower count outside 5,000-100,000 micro-influencer range")
    if row.get("engagement_rate_pct") in (None, "", "Not Available"):
        reasons.append("engagement rate unavailable from public video metrics")
    return not reasons, "Passed all configured checks" if not reasons else "; ".join(reasons)
