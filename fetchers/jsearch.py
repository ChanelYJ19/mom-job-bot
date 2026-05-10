import os
from typing import List

import requests

from fetchers.base import Fetcher
from normalize import Job


class JSearchFetcher(Fetcher):
    BASE_URL = "https://jsearch.p.rapidapi.com/search"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["JSEARCH_KEY"]

    def fetch(self, query: str, location: str) -> List[Job]:
        is_remote_run = location.lower() == "remote"
        params = {
            "query": query,
            "employment_types": "PARTTIME",
            "date_posted": "week",
            "num_pages": "1",
        }
        if is_remote_run:
            params["remote_jobs_only"] = "true"
        else:
            params["location"] = location

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        response = requests.get(self.BASE_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return [self._normalize(item) for item in data.get("data", [])]

    def _normalize(self, item: dict) -> Job:
        url = item.get("job_apply_link") or item.get("job_google_link") or ""
        return Job(
            id=Job.make_id("jsearch", url),
            source="jsearch",
            title=item.get("job_title", "").strip(),
            company=item.get("employer_name", "").strip(),
            location=self._location(item),
            is_remote=bool(item.get("job_is_remote")),
            employment_type=item.get("job_employment_type", "UNKNOWN"),
            posted_at=item.get("job_posted_at_datetime_utc"),
            url=url,
            description_snippet=Job.snippet(item.get("job_description", "")),
        )

    @staticmethod
    def _location(item: dict) -> str:
        if item.get("job_is_remote"):
            return "Remote"
        city = item.get("job_city", "")
        state = item.get("job_state", "")
        if city and state:
            return f"{city}, {state}"
        return item.get("job_country", "")
