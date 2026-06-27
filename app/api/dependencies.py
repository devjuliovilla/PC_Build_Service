from database import DDTechDB

from app.config import settings
from app.services.build_service import BuildService
from app.services.catalog_service import CatalogService
from app.services.job_service import JobService
from app.services.scraper_service import ScraperService


job_service = JobService()
db = DDTechDB(settings.database_path)
catalog_service = CatalogService(db)
build_service = BuildService(db)
scraper_service = ScraperService(settings, job_service)
