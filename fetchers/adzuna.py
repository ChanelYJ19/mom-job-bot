import os
from typing import List

import requests

from fetchers.base import Fetcher
from normalize import Job


class AdzunaFetcher(Fetcher):
    BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    def __init__(self, app_id: str | None = None, app_key: str | None = None):
        self.app_id = app_id or os.environ["ADZUNA_APP_ID"]
        self.app_key = app_key or os.environ["ADZUNA_APP_KEY"]

    def fetch(self, query: str, location: str) -> List[Job]:
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "max_days_old": "7",
            "results_per_page": "20",
            "content-type": "application/json",
        }
        if location.lower() != "remote":
            params["where"] = location
        else:
            params["what"] = f"{query} remote"

        response = requests.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return [self._normalize(item) for item in data.get("results", [])]

    def _normalize(self, item: dict) -> Job:
        url = item.get("redirect_url", "")
        title = item.get("title", "").strip()
        company = item.get("company", {}).get("display_name", "").strip()
        loc_data = item.get("location", {})
        area = loc_data.get("area", [])
        location = ", ".join(area[-2:]) if len(area) >= 2 else loc_data.get("display_name", "")
        is_remote = "remote" in title.lower() or "remote" in location.lower()
        contract_time = item.get("contract_time", "").upper()
        employment_type = "PART_TIME" if "part" in contract_time.lower() else "FULL_TIME" if "full" in contract_time.lower() else "UNKNOWN"
        description = item.get("description", "")

        return Job(
            id=Job.make_id("adzuna", url),
            source="adzuna",
            title=title,
            company=company,
            location="Remote" if is_remote else location,
            is_remote=is_remote,
            employment_type=employment_type,
            posted_at=item.get("created"),
            url=url,
            description_snippet=Job.snippet(description),
        )
