from fastapi import APIRouter

from app.api.dependencies import catalog_service, job_service
from app.api.schemas import StatusResponse
from app.config import settings


router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
def get_status():
    return catalog_service.get_status(job_service.latest_scraper_status(), settings.version)
