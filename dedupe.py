import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from normalize import Job

DB_PATH = Path(__file__).parent / "data" / "seen_jobs.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    url TEXT NOT NULL,
    first_seen_utc TEXT NOT NULL,
    last_seen_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS seen_title_company (
    key TEXT PRIMARY KEY,
    first_seen_utc TEXT NOT NULL
);
"""


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def filter_new(jobs: List[Job], db_path: Path = DB_PATH) -> List[Job]:
    """Return only jobs not seen before. Updates the DB in place."""
    conn = _connect(db_path)
    now = datetime.now(timezone.utc).isoformat()
    new_jobs: List[Job] = []

    for job in jobs:
        if _is_new(conn, job, now):
            new_jobs.append(job)
            _insert(conn, job, now)

    conn.commit()
    conn.close()
    return new_jobs


def _is_new(conn: sqlite3.Connection, job: Job, now: str) -> bool:
    row = conn.execute("SELECT id FROM seen_jobs WHERE id = ?", (job.id,)).fetchone()
    if row:
        conn.execute("UPDATE seen_jobs SET last_seen_utc = ? WHERE id = ?", (now, job.id))
        return False

    # fuzzy dedup: same (company, normalized_title) posted within 30 days
    key = f"{job.company.lower()}::{job.normalize_title(job.title)}"
    row = conn.execute(
        """
        SELECT first_seen_utc FROM seen_title_company
        WHERE key = ?
        AND julianday(?) - julianday(first_seen_utc) < 30
        """,
        (key, now),
    ).fetchone()
    return row is None


def _insert(conn: sqlite3.Connection, job: Job, now: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO seen_jobs (id, title, company, normalized_title, url, first_seen_utc, last_seen_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (job.id, job.title, job.company, job.normalize_title(job.title), job.url, now, now),
    )
    key = f"{job.company.lower()}::{job.normalize_title(job.title)}"
    conn.execute(
        "INSERT OR IGNORE INTO seen_title_company (key, first_seen_utc) VALUES (?, ?)",
        (key, now),
    )
