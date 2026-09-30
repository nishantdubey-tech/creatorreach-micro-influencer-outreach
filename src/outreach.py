"""Duplicate-safe simulated email queue and CSV outreach tracker."""
from __future__ import annotations
import csv, sqlite3
from datetime import datetime, timezone
from pathlib import Path

TRACKER_FIELDS = ["Influencer", "Email", "Message Generated", "Sent Date", "Status", "Channel", "Profile URL"]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def init_db(data_dir: Path) -> sqlite3.Connection:
    data_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(data_dir / "outreach.sqlite3")
    con.execute("CREATE TABLE IF NOT EXISTS outreach (profile_url TEXT PRIMARY KEY, email TEXT, message TEXT, generated_at_utc TEXT, sent_at_utc TEXT, status TEXT NOT NULL, channel TEXT NOT NULL DEFAULT 'email')")
    con.commit()
    return con


def simulate_send(data_dir: Path) -> dict:
    source = data_dir / "influencers.csv"
    if not source.exists(): raise RuntimeError("Run discovery first.")
    with source.open(encoding="utf-8", newline="") as handle: records = list(csv.DictReader(handle))
    con = init_db(data_dir); now = datetime.now(timezone.utc).isoformat(); queued = skipped = duplicates = 0
    for row in records:
        if row.get("filter_status") != "Passed": continue
        if con.execute("SELECT 1 FROM outreach WHERE profile_url=?", (row["profile_url"],)).fetchone():
            duplicates += 1; continue
        has_email = row.get("contact_email") not in (None, "", "Not Found")
        status = "SIMULATED_PENDING_REVIEW" if has_email else "SKIPPED_NO_PUBLIC_EMAIL"
        con.execute("INSERT INTO outreach(profile_url,email,message,generated_at_utc,sent_at_utc,status,channel) VALUES(?,?,?,?,?,?,?)",
                    (row["profile_url"], row.get("contact_email", "Not Found"), row.get("email_pitch", ""), now, None, status, "email"))
        if has_email: queued += 1
        else: skipped += 1
    con.commit()
    names = {r["profile_url"]: r["name"] for r in records}
    tracker = [{"Influencer": names.get(url, "Unknown"), "Email": email, "Message Generated": message,
                "Sent Date": sent or "", "Status": status, "Channel": channel, "Profile URL": url}
               for url,email,message,sent,status,channel in con.execute("SELECT profile_url,email,message,sent_at_utc,status,channel FROM outreach ORDER BY generated_at_utc")]
    write_csv(data_dir / "outreach.csv", tracker, TRACKER_FIELDS)
    # Compatibility alias for the original assignment output filename.
    write_csv(data_dir / "outreach_tracker.csv", tracker, TRACKER_FIELDS)
    con.close()
    return {"queued": queued, "skipped": skipped, "duplicates": duplicates, "tracker": tracker}
