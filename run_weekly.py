#!/usr/bin/env python3
"""Weekly job digest entry point. Run directly or via GitHub Actions."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import dedupe
import digest
import filter as job_filter
import mailer
from config import QUERIES, LOCATIONS
from fetchers.adzuna import AdzunaFetcher
from fetchers.craigslist import CraigslistFetcher
from fetchers.jsearch import JSearchFetcher
from fetchers.ratrace import RatRaceFetcher
from fetchers.remotive import RemotiveFetcher
from fetchers.themuse import TheMuseFetcher

LOG_PATH = Path(__file__).parent / "data" / "last_run.log"


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def build_fetchers() -> list:
    fetchers = []

    if os.environ.get("JSEARCH_KEY"):
        fetchers.append(JSearchFetcher())
        log("JSearch fetcher enabled")
    else:
        log("JSEARCH_KEY not set — skipping JSearch")

    if os.environ.get("ADZUNA_APP_ID") and os.environ.get("ADZUNA_APP_KEY"):
        fetchers.append(AdzunaFetcher())
        log("Adzuna fetcher enabled")
    else:
        log("ADZUNA credentials not set — skipping Adzuna")

    if os.environ.get("THEMUSE_API_KEY"):
        fetchers.append(TheMuseFetcher())
        log("The Muse fetcher enabled")
    else:
        log("THEMUSE_API_KEY not set — skipping The Muse (optional)")

    fetchers.append(RemotiveFetcher())
    log("Remotive fetcher enabled (no auth required)")

    fetchers.append(CraigslistFetcher())
    log("Craigslist RSS fetcher enabled")

    fetchers.append(RatRaceFetcher())
    log("Rat Race Rebellion RSS fetcher enabled")

    return fetchers


def main() -> None:
    log("=== Starting weekly job bot run ===")

    fetchers = build_fetchers()
    if not fetchers:
        log("ERROR: No fetchers available. Set at least JSEARCH_KEY.")
        sys.exit(1)

    all_jobs = []
    for fetcher in fetchers:
        name = fetcher.__class__.__name__
        log(f"Fetching from {name}...")
        try:
            jobs = fetcher.fetch_all(QUERIES, LOCATIONS)
            log(f"  {name}: {len(jobs)} raw results")
            all_jobs.extend(jobs)
        except Exception as exc:
            log(f"  {name}: ERROR — {exc}")

    log(f"Total raw jobs fetched: {len(all_jobs)}")

    filtered = job_filter.apply(all_jobs)
    log(f"After keyword/part-time filter: {len(filtered)}")

    new_jobs = dedupe.filter_new(filtered)
    log(f"After dedup: {len(new_jobs)} new jobs")

    subject, html_body, plain_body = digest.build(new_jobs)
    log(f"Digest built: {subject}")

    to_email = os.environ.get("TO_EMAIL")
    from_email = os.environ.get("FROM_EMAIL")
    if not to_email or not from_email:
        log("ERROR: TO_EMAIL and FROM_EMAIL must be set in environment.")
        sys.exit(1)

    mailer.send(subject, html_body, plain_body, to_email, from_email)
    log(f"Email sent to {to_email}")
    log("=== Run complete ===")


if __name__ == "__main__":
    main()
