from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import build_service
from app.api.schemas import BuildCreate, BuildUpdate, DecisionCreate, SlotUpdate, SlotUpsert


router = APIRouter(tags=["builds"])


@router.get("/builds")
def list_builds():
    return build_service.list_builds()


@router.post("/builds", status_code=status.HTTP_201_CREATED)
def create_build(payload: BuildCreate):
    return build_service.create_build(payload.name, payload.description)


@router.get("/builds/{build_id}")
def get_build(build_id: int):
    build = build_service.get_build(build_id)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build


@router.put("/builds/{build_id}")
def update_build(build_id: int, payload: BuildUpdate):
    build = build_service.update_build(build_id, payload.name, payload.description, payload.is_active)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_build(build_id: int):
    deleted = build_service.delete_build(build_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Build not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/builds/{build_id}/slots")
def create_slot(build_id: int, payload: SlotUpsert):
    slot = build_service.save_slot(build_id, payload.slot, payload.component_id, payload.is_locked, payload.notes)
    if not slot:
        raise HTTPException(status_code=404, detail="Build or component not found")
    return slot


@router.put("/builds/{build_id}/slots/{slot}")
def update_slot(build_id: int, slot: str, payload: SlotUpdate):
    updated_slot = build_service.update_slot(build_id, slot, payload.component_id, payload.is_locked, payload.notes)
    if not updated_slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return updated_slot


@router.delete("/builds/{build_id}/slots/{slot}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(build_id: int, slot: str):
    deleted = build_service.delete_slot(build_id, slot)
    if not deleted:
        raise HTTPException(status_code=404, detail="Slot not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/builds/{build_id}/slots/{slot}/decisions")
def create_decision(build_id: int, slot: str, payload: DecisionCreate):
    decision = build_service.save_decision(build_id, slot, payload.reason)
    if not decision:
        raise HTTPException(status_code=404, detail="Slot not found")
    return decision


@router.get("/builds/{build_id}/slots/{slot}/decisions")
def list_decisions(build_id: int, slot: str):
    return build_service.list_decisions(build_id, slot=slot)


@router.post("/builds/{build_id}/snapshot")
def create_snapshot(build_id: int):
    return build_service.create_snapshot(build_id)


@router.get("/builds/{build_id}/compare")
def compare_build(build_id: int):
    return build_service.compare_build(build_id)


@router.get("/builds/{build_id}/total")
def build_total(build_id: int):
    return build_service.total(build_id)
