import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from filter import apply
from normalize import Job


def make_job(title: str, description: str = "", employment_type: str = "PARTTIME", is_remote: bool = False) -> Job:
    return Job(
        id=Job.make_id("test", f"https://example.com/{title}"),
        source="test",
        title=title,
        company="Test Co",
        location="Remote" if is_remote else "Towson, MD",
        is_remote=is_remote,
        employment_type=employment_type,
        posted_at="2026-05-08T14:00:00Z",
        url=f"https://example.com/{title}",
        description_snippet=description,
    )


def test_matching_role_keyword_passes():
    jobs = [make_job("Medical Biller Part-Time", "billing and claims processing")]
    assert len(apply(jobs)) == 1


def test_no_role_keyword_filtered():
    jobs = [make_job("Software Engineer", "build web apps", employment_type="PARTTIME")]
    assert len(apply(jobs)) == 0


def test_exclude_manager_filtered():
    jobs = [make_job("Billing Manager", "billing department manager role")]
    assert len(apply(jobs)) == 0


def test_exclude_nurse_filtered():
    jobs = [make_job("Medical Biller - RN required", "must be a registered nurse rn lpn")]
    assert len(apply(jobs)) == 0


def test_full_time_only_filtered():
    jobs = [make_job("Medical Biller", "billing role", employment_type="FULLTIME", is_remote=False)]
    assert len(apply(jobs)) == 0


def test_remote_job_passes_without_parttime_flag():
    jobs = [make_job("Claims Processor", "process insurance claims", employment_type="UNKNOWN", is_remote=True)]
    assert len(apply(jobs)) == 1


def test_part_time_in_description_passes():
    jobs = [make_job("Front Desk Receptionist", "part time front desk role", employment_type="UNKNOWN")]
    assert len(apply(jobs)) == 1


def test_multiple_jobs_filtered_correctly():
    jobs = [
        make_job("Medical Biller Part-Time", "billing", employment_type="PARTTIME"),
        make_job("Director of Nursing", "rn lpn nursing director"),
        make_job("Payment Posting Specialist", "payment posting remote", is_remote=True),
    ]
    result = apply(jobs)
    assert len(result) == 2
    assert all(j.title != "Director of Nursing" for j in result)
