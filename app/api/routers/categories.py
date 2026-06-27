from fastapi import APIRouter

from app.api.dependencies import catalog_service


router = APIRouter(tags=["categories"])


@router.get("/categories")
def list_categories():
    return catalog_service.list_categories()
