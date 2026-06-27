from fastapi import APIRouter

from app.api.dependencies import catalog_service


router = APIRouter(tags=["chairs"])


@router.get("/chair-price-history/{chair_id}")
def chair_price_history(chair_id: str):
    return catalog_service.get_gaming_chair_price_history(chair_id)
