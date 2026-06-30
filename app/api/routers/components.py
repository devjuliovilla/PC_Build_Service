from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import catalog_service


router = APIRouter(tags=["components"])


@router.get("/components/search")
def search_components(q: str = Query(min_length=1), limit: int = Query(default=100, ge=1, le=10000)):
    return catalog_service.list_components(query=q, limit=limit)


@router.get("/components/latest")
def latest_components(only_in_stock: bool = False, limit: int = Query(default=100, ge=1, le=10000)):
    return catalog_service.get_latest_components(only_in_stock=only_in_stock, limit=limit)


@router.get("/components/category/{category}")
def components_by_category(category: str, limit: int = Query(default=250, ge=1, le=10000)):
    return catalog_service.list_components(category=category, limit=limit)


@router.get("/components/{component_id}")
def get_component(component_id: str):
    component = catalog_service.get_component(component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.get("/components")
def list_components(category: str | None = None, only_in_stock: bool = False, limit: int = Query(default=250, ge=1, le=10000)):
    return catalog_service.list_components(category=category, only_in_stock=only_in_stock, limit=limit)
