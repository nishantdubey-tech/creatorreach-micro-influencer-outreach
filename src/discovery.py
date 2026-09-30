"""Live creator discovery through the official YouTube Data API v3."""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from typing import Any
from .enrichment import enrich_channel

BASE = "https://www.googleapis.com/youtube/v3"
QUERIES = ["Indian fitness coach", "Indian home workout coach", "Indian strength training coach", "Indian yoga instructor", "Indian running coach", "Indian fitness nutrition"]


def api(path: str, **params: Any) -> dict:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("Set YOUTUBE_API_KEY (YouTube Data API v3) before live discovery.")
    params["key"] = key
    req = urllib.request.Request(f"{BASE}/{path}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "MicroInfluencerOutreachDemo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError(f"YouTube API request failed ({path}): {exc}") from exc


def discover_candidates(target: int = 50) -> list[dict]:
    """Fetch unique candidate channels, interleaved across query families."""
    query_results: dict[str, list[str]] = {}
    for query in QUERIES:
        token, ids = None, []
        while len(ids) < target:
            args = {"part": "snippet", "type": "channel", "q": query, "maxResults": 50, "relevanceLanguage": "en", "regionCode": "IN"}
            if token: args["pageToken"] = token
            result = api("search", **args)
            for item in result.get("items", []):
                cid = item.get("id", {}).get("channelId")
                if cid and cid not in ids: ids.append(cid)
                if len(ids) >= target: break
            token = result.get("nextPageToken")
            if not token: break
        query_results[query] = ids
    found: dict[str, str] = {}
    for offset in range(target):
        for query in QUERIES:
            pool = query_results.get(query, [])
            if offset < len(pool): found.setdefault(pool[offset], query)
            if len(found) >= target: break
        if len(found) >= target: break
    ids = list(found)
    channels = []
    for start in range(0, len(ids), 50):
        response = api("channels", part="snippet,statistics,contentDetails", id=",".join(ids[start:start+50]))
        channels.extend(response.get("items", []))
    return [enrich_channel(c, found[c["id"]], api) for c in channels]
