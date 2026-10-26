from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    authenticated: bool


class HealthResponse(BaseModel):
    status: str


class RecordsResponse(BaseModel):
    items: list[dict[str, Any]]


class MeterResponse(BaseModel):
    meter: dict[str, Any]


class ConsumptionResponse(BaseModel):
    meter_id: str
    records: list[dict[str, Any]]


class HierarchyResponse(BaseModel):
    hierarchy: Any


class ErrorResponse(BaseModel):
    detail: str
