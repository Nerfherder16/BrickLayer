from __future__ import annotations


def test_worker_settings_job_timeout():
    from backend.app.worker import WorkerSettings

    assert WorkerSettings.job_timeout == 300


def test_worker_settings_max_jobs():
    from backend.app.worker import WorkerSettings

    assert WorkerSettings.max_jobs == 10


def test_worker_settings_has_redis_settings_or_functions():
    from backend.app.worker import WorkerSettings

    has_redis = hasattr(WorkerSettings, "redis_settings")
    has_functions = hasattr(WorkerSettings, "functions")
    assert has_redis or has_functions
