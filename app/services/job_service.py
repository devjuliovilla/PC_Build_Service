import threading
import uuid
from datetime import datetime, timezone


class JobService:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs = {}

    def create_job(self, job_type):
        job_id = str(uuid.uuid4())
        job = {
            "jobId": job_id,
            "type": job_type,
            "status": "Pending",
            "createdAt": self._now(),
            "startedAt": None,
            "finishedAt": None,
            "duration": None,
            "componentsUpdated": 0,
            "error": None,
        }
        with self._lock:
            self._jobs[job_id] = job
        return job

    def start_job(self, job_id):
        with self._lock:
            job = self._jobs[job_id]
            job["status"] = "Running"
            job["startedAt"] = self._now()
            return dict(job)

    def complete_job(self, job_id, components_updated=0):
        with self._lock:
            job = self._jobs[job_id]
            job["status"] = "Completed"
            job["finishedAt"] = self._now()
            job["componentsUpdated"] = components_updated
            job["duration"] = self._duration(job)
            return dict(job)

    def fail_job(self, job_id, error):
        with self._lock:
            job = self._jobs[job_id]
            job["status"] = "Failed"
            job["finishedAt"] = self._now()
            job["error"] = str(error)
            job["duration"] = self._duration(job)
            return dict(job)

    def get_job(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def latest_scraper_status(self):
        with self._lock:
            scraper_jobs = [job for job in self._jobs.values() if job["type"] == "scraper.update"]
            if not scraper_jobs:
                return "Idle"
            latest = max(scraper_jobs, key=lambda item: item["createdAt"])
            return latest["status"]

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _duration(self, job):
        if not job["startedAt"] or not job["finishedAt"]:
            return None
        started_at = datetime.fromisoformat(job["startedAt"])
        finished_at = datetime.fromisoformat(job["finishedAt"])
        return (finished_at - started_at).total_seconds()
