from abc import ABC, abstractmethod
from typing import List
from normalize import Job


class Fetcher(ABC):
    """Abstract base for all job source fetchers."""

    @abstractmethod
    def fetch(self, query: str, location: str) -> List[Job]:
        """Return a list of normalized Jobs for the given query + location."""
        ...

    def fetch_all(self, queries: List[str], locations: List[str]) -> List[Job]:
        jobs: List[Job] = []
        for query in queries:
            for location in locations:
                try:
                    jobs.extend(self.fetch(query, location))
                except Exception as exc:
                    print(f"[{self.__class__.__name__}] failed for query={query!r} location={location!r}: {exc}")
        return jobs
