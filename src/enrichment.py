"""Profile metrics, public contact extraction, and content context."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any, Callable

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
URL_RE = re.compile(r"https?://[^\s<>\]]+", re.I)


def enrich_channel(channel: dict[str, Any], search_query: str, api_call: Callable[..., dict]) -> dict[str, Any]:
    snippet = channel.get("snippet", {})
    stats = channel.get("statistics", {})
    uploads = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    videos = []
    if uploads:
        page = api_call("playlistItems", part="contentDetails", playlistId=uploads, maxResults=10)
        video_ids = [x.get("contentDetails", {}).get("videoId") for x in page.get("items", [])]
        video_ids = [x for x in video_ids if x]
        if video_ids:
            videos = api_call("videos", part="snippet,statistics", id=",".join(video_ids)).get("items", [])
    followers = int(stats.get("subscriberCount", 0) or 0)
    metric_videos = [v for v in videos if v.get("statistics", {}).get("likeCount") is not None and v.get("statistics", {}).get("commentCount") is not None]
    engagement = None
    if followers and metric_videos:
        total_interactions = sum(int(v["statistics"].get("likeCount", 0)) + int(v["statistics"].get("commentCount", 0)) for v in metric_videos)
        engagement = round(100 * total_interactions / len(metric_videos) / followers, 2)
    titles = [v.get("snippet", {}).get("title", "").strip() for v in videos if v.get("snippet", {}).get("title")]
    description = snippet.get("description", "")
    email_match = EMAIL_RE.search(description)
    email = email_match.group(0) if email_match and "example." not in email_match.group(0).lower() else "Not Found"
    urls = [u.rstrip(".,);\"'") for u in URL_RE.findall(description)]
    website = next((u for u in urls if "youtube.com" not in u.lower() and "youtu.be" not in u.lower()), "Not Found")
    content_context = " ".join([snippet.get("title", ""), description, *titles])
    category = "Fitness" if re.search(r"fit|workout|yoga|gym|train|run|nutrition|health|exercise", content_context, re.I) else "Other"
    handle = snippet.get("customUrl", "")
    profile = f"https://www.youtube.com/{handle}" if handle else f"https://www.youtube.com/channel/{channel['id']}"
    return {
        "name": snippet.get("title", "Unknown"), "platform": "YouTube", "profile_url": profile,
        "followers": followers, "engagement_rate_pct": engagement if engagement is not None else "Not Available",
        "niche": category, "content_themes": " | ".join(titles[:5]) or "Not Available",
        "contact_email": email, "website": website,
        "audience_age": "Not Available", "audience_gender": "Not Available",
        "audience_geography": "India (search region; audience location not verified)",
        "channel_country": snippet.get("country", "Not Available"),
        "source": "YouTube Data API v3", "source_url": profile,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "recent_video_count": len(videos), "engagement_sample_count": len(metric_videos),
        "search_query": search_query, "channel_description": description[:500],
        "youtube_channel_id": channel["id"],
        "hidden_subscriber_count": bool(stats.get("hiddenSubscriberCount", False)),
    }
