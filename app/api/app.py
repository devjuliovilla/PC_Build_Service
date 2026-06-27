from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routers import builds, categories, components, health, history, scraper, status
from app.config import settings
from app.logging import configure_logging


def create_app():
    configure_logging(settings.log_level)

    app = FastAPI(
        title="DDTech API",
        version=settings.version,
        description="Servicio REST para scraping, catalogo y administracion de builds DDTech.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    app.include_router(status.router)
    app.include_router(health.router)
    app.include_router(categories.router)
    app.include_router(components.router)
    app.include_router(history.router)
    app.include_router(builds.router)
    app.include_router(scraper.router)
    return app
