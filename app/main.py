from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from app.client import (
    PortalConfigurationError,
    PortalError,
    UrjaPortalClient,
)
from app.config import Settings
from app.models import (
    ConsumptionResponse,
    HealthResponse,
    HierarchyResponse,
    LoginRequest,
    LoginResponse,
    MeterResponse,
    RecordsResponse,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.portal_client = UrjaPortalClient(config)
        try:
            yield
        finally:
            app.state.portal_client.close()

    app = FastAPI(
        title="Flock Energy - Urja Meter Ops API",
        version="1.0.0",
        description=(
            "A REST wrapper for the Urja Meter Ops portal. Upstream routes and "
            "authentication fields are configurable because the portal protocol "
            "must be verified in the target environment."
        ),
        lifespan=lifespan,
    )
    def portal(request: Request) -> UrjaPortalClient:
        return request.app.state.portal_client

    def call_upstream(operation: Any) -> Any:
        try:
            return operation()
        except PortalConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except PortalError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post(
        "/api/v1/auth/login",
        response_model=LoginResponse,
        tags=["auth"],
        responses={
            502: {"description": "Portal login failed"},
            503: {"description": "Portal credentials are not configured"},
        },
    )
    def login(payload: LoginRequest, request: Request) -> LoginResponse:
        authenticated = call_upstream(
            lambda: portal(request).login(payload.username, payload.password)
        )
        return LoginResponse(authenticated=authenticated)

    @app.get(
        "/api/v1/meters",
        response_model=RecordsResponse,
        tags=["meters"],
        responses={
            502: {"description": "Portal returned an error or unexpected data"},
            503: {"description": "Portal credentials are not configured"},
        },
    )
    def meters(request: Request) -> RecordsResponse:
        items = call_upstream(lambda: portal(request).get_meters())
        return RecordsResponse(items=items)

    @app.get(
        "/api/v1/meters/{meter_id}",
        response_model=MeterResponse,
        tags=["meters"],
        responses={
            502: {"description": "Portal returned an error or unexpected data"},
            503: {"description": "Portal credentials are not configured"},
        },
    )
    def meter(meter_id: str, request: Request) -> MeterResponse:
        item = call_upstream(lambda: portal(request).get_meter(meter_id))
        return MeterResponse(meter=item)

    @app.get(
        "/api/v1/meters/{meter_id}/consumption",
        response_model=ConsumptionResponse,
        tags=["meters"],
        responses={
            502: {"description": "Portal returned an error or unexpected data"},
            503: {"description": "Portal credentials are not configured"},
        },
    )
    def consumption(meter_id: str, request: Request) -> ConsumptionResponse:
        records = call_upstream(
            lambda: portal(request).get_consumption(meter_id)
        )
        return ConsumptionResponse(meter_id=meter_id, records=records)

    @app.get(
        "/api/v1/hierarchy",
        response_model=HierarchyResponse,
        tags=["hierarchy"],
        responses={
            502: {"description": "Portal returned an error"},
            503: {"description": "Portal credentials are not configured"},
        },
    )
    def hierarchy(request: Request) -> HierarchyResponse:
        result = call_upstream(lambda: portal(request).get_hierarchy())
        return HierarchyResponse(hierarchy=result)

    return app


app = create_app()
