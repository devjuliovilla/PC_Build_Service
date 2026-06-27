from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import job_service, scraper_service
from app.api.schemas import JobResponse, ScraperUpdateRequest


router = APIRouter(tags=["scraper"])


@router.post("/scraper/update", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_scraper(payload: ScraperUpdateRequest):
    return scraper_service.queue_update(fallback=payload.fallback, test_run=payload.test_run)


@router.post("/scraper/chairs/update", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_chairs_scraper():
    return scraper_service.queue_chairs_update()


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
