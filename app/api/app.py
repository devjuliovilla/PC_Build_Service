from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routers import builds, categories, chair_history, chairs, components, health, history, scraper, status
from app.config import settings
from app.logging import configure_logging


def create_app():
    configure_logging(settings.log_level)

    app = FastAPI(
        title="PC_Build_Service",
        version=settings.version,
        description="Servicio REST para catalogo, builds persistentes y ejecucion asincrona del scraper de componentes.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    app.include_router(status.router)
    app.include_router(health.router)
    app.include_router(categories.router)
    app.include_router(components.router)
    app.include_router(chairs.router)
    app.include_router(history.router)
    app.include_router(chair_history.router)
    app.include_router(builds.router)
    app.include_router(scraper.router)
    return app
