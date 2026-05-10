import os
from typing import List

import requests

from fetchers.base import Fetcher
from normalize import Job


class TheMuseFetcher(Fetcher):
    BASE_URL = "https://www.themuse.com/api/public/jobs"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("THEMUSE_API_KEY", "")

    def fetch(self, query: str, location: str) -> List[Job]:
        params: dict = {"page": 0, "descending": "true"}
        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        query_lower = query.lower()
        jobs: List[Job] = []
        for item in data.get("results", []):
            title = item.get("name", "")
            if not any(kw in title.lower() for kw in query_lower.split()):
                continue
            jobs.append(self._normalize(item))
        return jobs

    def _normalize(self, item: dict) -> Job:
        url = item.get("refs", {}).get("landing_page", "")
        title = item.get("name", "").strip()
        company = item.get("company", {}).get("name", "").strip()
        locations = item.get("locations", [])
        location_str = locations[0].get("name", "") if locations else "Unknown"
        is_remote = "remote" in location_str.lower() or "flexible" in location_str.lower()
        levels = item.get("levels", [])
        level_names = [l.get("name", "").lower() for l in levels]

        return Job(
            id=Job.make_id("themuse", url),
            source="themuse",
            title=title,
            company=company,
            location="Remote" if is_remote else location_str,
            is_remote=is_remote,
            employment_type="UNKNOWN",
            posted_at=item.get("publication_date"),
            url=url,
            description_snippet=Job.snippet(item.get("contents", "")),
        )
