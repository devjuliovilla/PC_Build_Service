from fastapi import APIRouter

from app.api.dependencies import catalog_service


router = APIRouter(tags=["history"])


@router.get("/price-history/{component_id}")
def price_history(component_id: str):
    return catalog_service.get_price_history(component_id)
