from typing import Any

from pydantic import BaseModel, Field


class BuildCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class BuildUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SlotUpsert(BaseModel):
    slot: str
    component_id: str
    is_locked: bool = False
    notes: str | None = None


class SlotUpdate(BaseModel):
    component_id: str
    is_locked: bool | None = None
    notes: str | None = None


class DecisionCreate(BaseModel):
    reason: str = Field(min_length=1)


class ScraperUpdateRequest(BaseModel):
    fallback: bool = False
    test_run: bool = False


class MessageResponse(BaseModel):
    message: str


class StatusResponse(BaseModel):
    components_count: int
    categories_count: int
    builds_count: int
    last_update: str | None
    scraper_status: str
    version: str


class JobResponse(BaseModel):
    jobId: str
    type: str | None = None
    status: str
    createdAt: str
    startedAt: str | None = None
    finishedAt: str | None = None
    duration: float | None = None
    componentsUpdated: int = 0
    error: str | None = None


class BulkSlotsRequest(BaseModel):
    slots: dict[str, str] = Field(description="Map of slot name to component ID")


class GenericDictResponse(BaseModel):
    data: dict[str, Any]
