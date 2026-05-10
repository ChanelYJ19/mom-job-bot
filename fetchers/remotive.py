from typing import List

import requests

from fetchers.base import Fetcher
from normalize import Job

CATEGORIES = ["customer-support", "all-others"]


class RemotiveFetcher(Fetcher):
    BASE_URL = "https://remotive.com/api/remote-jobs"

    def fetch(self, query: str, location: str) -> List[Job]:
        if location.lower() != "remote":
            return []  # remotive is remote-only; skip for local searches

        jobs: List[Job] = []
        for category in CATEGORIES:
            try:
                jobs.extend(self._fetch_category(query, category))
            except Exception as exc:
                print(f"[remotive] category={category} failed: {exc}")
        return jobs

    def _fetch_category(self, query: str, category: str) -> List[Job]:
        params = {"category": category, "search": query}
        response = requests.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return [self._normalize(item) for item in data.get("jobs", [])]

    def _normalize(self, item: dict) -> Job:
        url = item.get("url", "")
        return Job(
            id=Job.make_id("remotive", url),
            source="remotive",
            title=item.get("title", "").strip(),
            company=item.get("company_name", "").strip(),
            location="Remote",
            is_remote=True,
            employment_type="UNKNOWN",
            posted_at=item.get("publication_date"),
            url=url,
            description_snippet=Job.snippet(item.get("description", "")),
        )
