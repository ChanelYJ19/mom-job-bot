from typing import List

from config import EXCLUDE_KEYWORDS, ROLE_KEYWORDS, TOWSON_AREA_KEYWORDS
from normalize import Job


def apply(jobs: List[Job]) -> List[Job]:
    return [j for j in jobs if _passes(j)]


def _passes(job: Job) -> bool:
    haystack = f"{job.title} {job.description_snippet}".lower()

    if not any(kw in haystack for kw in ROLE_KEYWORDS):
        return False

    if any(kw in haystack for kw in EXCLUDE_KEYWORDS):
        return False

    if not _is_part_time(job):
        return False

    if not _is_local_or_remote(job):
        return False

    return True


def _is_part_time(job: Job) -> bool:
    if job.employment_type in ("PARTTIME", "PART_TIME"):
        return True
    if job.is_remote:
        return True
    haystack = f"{job.title} {job.description_snippet}".lower()
    return "part" in haystack or " pt " in haystack or "pt," in haystack


def _is_local_or_remote(job: Job) -> bool:
    if job.is_remote:
        return True
    location = job.location.lower()
    return any(kw in location for kw in TOWSON_AREA_KEYWORDS)
