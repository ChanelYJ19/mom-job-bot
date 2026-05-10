import json
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers.jsearch import JSearchFetcher
from normalize import Job

FIXTURE = Path(__file__).parent / "fixtures" / "sample_jsearch_response.json"


def make_mock_response(data: dict) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text())


def test_normalizes_all_items():
    fixture = load_fixture()
    fetcher = JSearchFetcher(api_key="test-key")

    with patch("fetchers.jsearch.requests.get", return_value=make_mock_response(fixture)):
        jobs = fetcher.fetch("medical billing", "Towson, MD")

    assert len(jobs) == 3


def test_local_job_has_correct_fields():
    fixture = load_fixture()
    fetcher = JSearchFetcher(api_key="test-key")

    with patch("fetchers.jsearch.requests.get", return_value=make_mock_response(fixture)):
        jobs = fetcher.fetch("medical billing", "Towson, MD")

    local_job = jobs[0]
    assert local_job.source == "jsearch"
    assert local_job.title == "Medical Biller (Part-Time)"
    assert local_job.company == "Towson Family Practice"
    assert local_job.location == "Towson, MD"
    assert local_job.is_remote is False
    assert local_job.employment_type == "PARTTIME"
    assert local_job.url == "https://example.com/apply/abc123"
    assert "biller" in local_job.description_snippet.lower()


def test_remote_job_has_remote_location():
    fixture = load_fixture()
    fetcher = JSearchFetcher(api_key="test-key")

    with patch("fetchers.jsearch.requests.get", return_value=make_mock_response(fixture)):
        jobs = fetcher.fetch("payment posting", "Remote")

    remote_job = jobs[1]
    assert remote_job.is_remote is True
    assert remote_job.location == "Remote"


def test_id_is_stable_sha256():
    url = "https://example.com/apply/abc123"
    id1 = Job.make_id("jsearch", url)
    id2 = Job.make_id("jsearch", url)
    assert id1 == id2
    assert len(id1) == 64  # sha256 hex


def test_normalize_title():
    assert Job.normalize_title("Medical Biller (Part-Time)") == "medical biller"
    assert Job.normalize_title("Front Desk Receptionist - Remote") == "front desk receptionist"


def test_snippet_truncates():
    long_text = "x " * 300
    result = Job.snippet(long_text)
    assert len(result) <= 400
