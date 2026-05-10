from typing import List

import feedparser

from config import TOWSON_AREA_KEYWORDS
from fetchers.base import Fetcher
from normalize import Job

RSS_BASE = "https://baltimore.craigslist.org/search/jjj"

CRAIGSLIST_QUERIES = [
    "medical billing",
    "front desk medical",
    "payment posting",
    "medical receptionist",
    "file clerk",
]


class CraigslistFetcher(Fetcher):
    def fetch(self, query: str, location: str) -> List[Job]:
        url = f"{RSS_BASE}?query={query.replace(' ', '+')}&format=rss"
        feed = feedparser.parse(url)
        jobs: List[Job] = []

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", None)

            combined = f"{title} {summary}".lower()
            if not any(kw in combined for kw in TOWSON_AREA_KEYWORDS):
                continue

            jobs.append(Job(
                id=Job.make_id("craigslist", link),
                source="craigslist",
                title=title.strip(),
                company="(via Craigslist)",
                location=self._extract_location(summary),
                is_remote=False,
                employment_type="UNKNOWN",
                posted_at=published,
                url=link,
                description_snippet=Job.snippet(summary),
            ))

        return jobs

    @staticmethod
    def _extract_location(summary: str) -> str:
        summary_lower = summary.lower()
        for kw in TOWSON_AREA_KEYWORDS:
            if kw in summary_lower:
                return kw.title() + ", MD"
        return "Baltimore Area, MD"
