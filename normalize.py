import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Job:
    id: str
    source: str
    title: str
    company: str
    location: str
    is_remote: bool
    employment_type: str  # PART_TIME | FULL_TIME | UNKNOWN
    posted_at: Optional[str]  # ISO-8601 UTC string or None
    url: str
    description_snippet: str

    @staticmethod
    def make_id(source: str, url: str) -> str:
        key = f"{source}::{url}"
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def normalize_title(title: str) -> str:
        """Lowercase, strip punctuation, remove noise words — used for fuzzy dedup."""
        title = title.lower()
        title = re.sub(r"[^\w\s]", " ", title)
        noise = {"part", "time", "pt", "remote", "the", "a", "an", "and", "or", "of", "in", "at"}
        return " ".join(w for w in title.split() if w not in noise)

    @staticmethod
    def snippet(text: str, length: int = 400) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text[:length]
