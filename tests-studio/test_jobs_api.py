import datetime
import os

import pytest
from fastapi.testclient import TestClient

import database
from studio.app import app, _job_percent

TEST_DB_PATH = "data/test_story_studio_jobs.db"


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", TEST_DB_PATH)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    database.init_db()
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


client = TestClient(app)


def test_get_video_jobs_filters_by_transition():
    """Only ltx25_t2v rows come back -- stitched full-story videos don't."""
    ltx_id = database.create_video_record("story_a", "ltx25_t2v", 4.0, scene_index=6)
    database.create_video_record("story_a", "audio_crossfade", 12.0)

    jobs = database.get_video_jobs()

    assert len(jobs) == 1
    assert jobs[0]["id"] == ltx_id
    assert jobs[0]["scene_index"] == 6


def test_job_percent_completed_and_failed_are_fixed():
    assert _job_percent("completed", "2020-01-01 00:00:00") == 100
    assert _job_percent("failed", "2020-01-01 00:00:00") == 0


def test_job_percent_running_scales_with_elapsed_time():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    just_started = _job_percent("pending", now)
    assert 0 <= just_started <= 5

    long_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    assert _job_percent("pending", long_ago) == 99


def test_api_jobs_reports_status_and_file_url():
    completed_id = database.create_video_record("geronimo", "ltx25_t2v", 4.0, scene_index=3)
    database.update_video_record(completed_id, "clip.mp4", status="completed")

    running_id = database.create_video_record("geronimo", "ltx25_t2v", 4.0, scene_index=4)

    failed_id = database.create_video_record("geronimo", "ltx25_t2v", 4.0, scene_index=5)
    database.update_video_record(failed_id, None, status="failed")

    response = client.get("/api/jobs")
    assert response.status_code == 200
    jobs_by_id = {job["id"]: job for job in response.json()["jobs"]}

    completed = jobs_by_id[completed_id]
    assert completed["status"] == "completed"
    assert completed["percent"] == 100
    assert completed["file_url"] == "/images/geronimo/videos/clip.mp4"

    running = jobs_by_id[running_id]
    assert running["status"] == "running"  # 'pending' in the DB, "running" to the UI
    assert running["file_url"] is None

    failed = jobs_by_id[failed_id]
    assert failed["status"] == "failed"
    assert failed["percent"] == 0
    assert failed["file_url"] is None
