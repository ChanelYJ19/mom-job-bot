from typing import List

import feedparser

from config import ROLE_KEYWORDS
from fetchers.base import Fetcher
from normalize import Job

RSS_URL = "https://ratracerebellion.com/feed/"


class RatRaceFetcher(Fetcher):
    def fetch(self, query: str, location: str) -> List[Job]:
        if location.lower() != "remote":
            return []  # Rat Race Rebellion is remote/WFH only

        feed = feedparser.parse(RSS_URL)
        jobs: List[Job] = []

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", None)

            combined = f"{title} {summary}".lower()
            if not any(kw in combined for kw in ROLE_KEYWORDS):
                continue

            jobs.append(Job(
                id=Job.make_id("ratrace", link),
                source="ratrace",
                title=title.strip(),
                company="(via Rat Race Rebellion)",
                location="Remote",
                is_remote=True,
                employment_type="UNKNOWN",
                posted_at=published,
                url=link,
                description_snippet=Job.snippet(summary),
            ))

        return jobs
