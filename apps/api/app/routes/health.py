from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse, tags=["System"])
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="library-yui-api")
