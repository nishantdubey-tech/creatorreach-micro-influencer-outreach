"""Orchestrate discovery, filtering, enrichment, personalization, and tracking."""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from .discovery import discover_candidates
from .filtering import classify
from .outreach import simulate_send, write_csv
from .personalization import personalize

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIELDS = ["name","platform","followers","engagement_rate_pct","niche","profile_url","contact_email","content_themes","website","audience_age","audience_gender","audience_geography","channel_country","source","source_url","retrieved_at_utc","recent_video_count","engagement_sample_count","search_query","filter_status","filter_reason","personalization_method","email_pitch","instagram_dm"]


def read_records() -> list[dict]:
    path=DATA/"influencers.csv"
    if not path.exists(): raise RuntimeError("No dataset found. Run live discovery first.")
    with path.open(encoding="utf-8",newline="") as handle: return list(csv.DictReader(handle))


def save_records(rows: list[dict]) -> None: write_csv(DATA/"influencers.csv", rows, FIELDS)


def filter_records(rows: list[dict]) -> list[dict]:
    for row in rows:
        passed, reason = classify(row)
        row["filter_status"] = "Passed" if passed else "Failed"
        row["filter_reason"] = reason
    return rows


def personalize_records(rows: list[dict]) -> list[dict]:
    for row in rows:
        if row.get("filter_status") == "Passed":
            row["email_pitch"], row["instagram_dm"], row["personalization_method"] = personalize(row)
        else:
            row["email_pitch"], row["instagram_dm"] = "", ""
            row["personalization_method"] = "Not generated: failed filter"
    return rows


def write_shortlist(rows: list[dict]) -> list[dict]:
    shortlisted=[r for r in rows if r.get("filter_status")=="Passed"]
    write_csv(DATA/"shortlisted_messages.csv", shortlisted, FIELDS)
    return shortlisted


def discover_and_prepare(target: int = 50) -> list[dict]:
    """Discover new profiles and merge them into the saved dataset by URL."""
    existing = read_records() if (DATA/"influencers.csv").exists() else []
    merged = {r.get("profile_url") or r.get("name", ""): r for r in existing}
    for row in discover_candidates(target):
        key = row.get("profile_url") or row.get("name", "")
        merged[key] = row
    rows=list(merged.values())
    rows=personalize_records(filter_records(rows))
    save_records(rows); write_shortlist(rows)
    return rows


def refresh_filter() -> list[dict]:
    rows=personalize_records(filter_records(read_records()))
    save_records(rows); write_shortlist(rows)
    return rows


def refresh_messages() -> list[dict]:
    rows=personalize_records(read_records())
    save_records(rows); write_shortlist(rows)
    return rows


def main() -> None:
    parser=argparse.ArgumentParser(description="Live YouTube fitness creator discovery with safe simulated outreach.")
    sub=parser.add_subparsers(dest="command",required=True)
    discover=sub.add_parser("discover"); discover.add_argument("--target",type=int,default=50)
    sub.add_parser("filter"); sub.add_parser("personalize"); sub.add_parser("simulate-send")
    args=parser.parse_args()
    try:
        if args.command=="discover":
            rows=discover_and_prepare(max(1,args.target))
            print(f"Fetched {len(rows)} unique profiles; {sum(r['filter_status']=='Passed' for r in rows)} passed.")
        elif args.command=="filter":
            rows=refresh_filter(); print(f"Filtered {len(rows)} profiles; {sum(r['filter_status']=='Passed' for r in rows)} passed.")
        elif args.command=="personalize":
            rows=refresh_messages(); print(f"Generated messages for {sum(r['filter_status']=='Passed' for r in rows)} qualified profiles.")
        else:
            result=simulate_send(DATA); print(f"Queued {result['queued']}; skipped for missing public email {result['skipped']}; duplicates skipped {result['duplicates']}. No emails were sent.")
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise SystemExit(1)

if __name__=="__main__": main()
