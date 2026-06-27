from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import catalog_service


router = APIRouter(tags=["chairs"])


@router.get("/chairs/search")
def search_chairs(q: str = Query(min_length=1), limit: int = Query(default=100, ge=1, le=500)):
    return catalog_service.list_gaming_chairs(query=q, limit=limit)


@router.get("/chairs/latest")
def latest_chairs(only_in_stock: bool = False, limit: int = Query(default=100, ge=1, le=500)):
    return catalog_service.get_latest_gaming_chairs(only_in_stock=only_in_stock, limit=limit)


@router.get("/chairs/{chair_id}")
def get_chair(chair_id: str):
    chair = catalog_service.get_gaming_chair(chair_id)
    if not chair:
        raise HTTPException(status_code=404, detail="Chair not found")
    return chair


@router.get("/chairs")
def list_chairs(only_in_stock: bool = False, limit: int = Query(default=250, ge=1, le=500)):
    return catalog_service.list_gaming_chairs(only_in_stock=only_in_stock, limit=limit)
