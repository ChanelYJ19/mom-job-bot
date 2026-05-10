import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dedupe import filter_new
from normalize import Job


def make_job(url: str, title: str = "Medical Biller", company: str = "Test Co") -> Job:
    return Job(
        id=Job.make_id("test", url),
        source="test",
        title=title,
        company=company,
        location="Towson, MD",
        is_remote=False,
        employment_type="PARTTIME",
        posted_at="2026-05-08T14:00:00Z",
        url=url,
        description_snippet="Medical billing part-time role.",
    )


def test_new_job_passes_through():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db = Path(f.name)
    job = make_job("https://example.com/job/1")
    result = filter_new([job], db_path=db)
    assert len(result) == 1
    assert result[0].url == "https://example.com/job/1"


def test_seen_job_deduped():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db = Path(f.name)
    job = make_job("https://example.com/job/2")
    filter_new([job], db_path=db)  # first run: insert
    result = filter_new([job], db_path=db)  # second run: dedupe
    assert len(result) == 0


def test_fuzzy_dedup_same_title_company():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db = Path(f.name)
    job1 = make_job("https://example.com/job/3", title="Medical Biller (Part-Time)", company="Acme Health")
    job2 = make_job("https://example.com/job/4", title="Medical Biller — PT", company="Acme Health")
    filter_new([job1], db_path=db)
    result = filter_new([job2], db_path=db)
    assert len(result) == 0  # same normalized title + company


def test_different_companies_both_pass():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db = Path(f.name)
    job1 = make_job("https://example.com/job/5", title="Medical Biller", company="Company A")
    job2 = make_job("https://example.com/job/6", title="Medical Biller", company="Company B")
    result = filter_new([job1, job2], db_path=db)
    assert len(result) == 2
