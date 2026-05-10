from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from jinja2 import Environment, FileSystemLoader

from normalize import Job

TEMPLATE_DIR = Path(__file__).parent / "templates"


def build(jobs: List[Job]) -> Tuple[str, str, str]:
    """Return (subject, html_body, plain_body) for the digest email."""
    local_jobs = sorted(
        [j for j in jobs if not j.is_remote],
        key=lambda j: j.posted_at or "",
        reverse=True,
    )
    remote_jobs = sorted(
        [j for j in jobs if j.is_remote],
        key=lambda j: j.posted_at or "",
        reverse=True,
    )

    run_date = datetime.now(timezone.utc).strftime("%a %b %-d")
    total = len(jobs)

    subject = (
        f"Mom's Job Digest — {total} new listing{'s' if total != 1 else ''} — {run_date}"
        if total > 0
        else f"Mom's Job Digest — No new listings — {run_date}"
    )

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("digest.html.j2")
    html_body = template.render(
        local_jobs=local_jobs,
        remote_jobs=remote_jobs,
        run_date=run_date,
        total=total,
    )

    plain_body = _plain(local_jobs, remote_jobs, run_date, total)
    return subject, html_body, plain_body


def _plain(local_jobs: List[Job], remote_jobs: List[Job], run_date: str, total: int) -> str:
    lines = [
        f"Mom's Job Digest — {run_date}",
        "",
        "Hi Mom — here are this week's new part-time openings near Towson and remote.",
        "",
    ]

    if local_jobs:
        lines += [f"TOWSON / BALTIMORE AREA ({len(local_jobs)})", "=" * 40]
        for job in local_jobs:
            lines += _job_lines(job)

    if remote_jobs:
        lines += [f"REMOTE ({len(remote_jobs)})", "=" * 40]
        for job in remote_jobs:
            lines += _job_lines(job)

    if not local_jobs and not remote_jobs:
        lines.append("No new postings this week — the bot is still running, check back Monday.")

    lines += ["", "-" * 40, f"Bot built with love by Chanel · {total} new listing{'s' if total != 1 else ''} this week"]
    return "\n".join(lines)


def _job_lines(job: Job) -> List[str]:
    posted = job.posted_at[:10] if job.posted_at else "Unknown date"
    return [
        f"",
        f"▸ {job.title} — {job.company}",
        f"  {job.location} · Part-time · {posted}",
        f"  \"{job.description_snippet[:200]}\"",
        f"  Apply: {job.url}",
    ]
