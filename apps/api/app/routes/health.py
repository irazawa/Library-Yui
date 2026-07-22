from fastapi import APIRouter
from pydantic import BaseModel

from app.downloader import is_downloads_enabled
from app.routes.library import MAX_UPLOAD_BYTES
from app.storage import LIBRARY_DIR, STORAGE_DIRS

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


class ConfigResponse(BaseModel):
    downloads_enabled: bool
    max_upload_bytes: int
    library_dirs: dict[str, str]


@router.get("/health", response_model=HealthResponse, tags=["System"])
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="library-yui-api")


@router.get("/config", response_model=ConfigResponse, tags=["System"])
def get_config() -> ConfigResponse:
    """Return runtime configuration visible to clients.

    This intentionally exposes only non-secret operational settings: whether
    real downloads are enabled, the upload size cap, and the resolved library
    storage directories.
    """

    library_dirs = {"library": str(LIBRARY_DIR.resolve())}
    library_dirs.update({name: str(path.resolve()) for name, path in STORAGE_DIRS.items()})
    return ConfigResponse(
        downloads_enabled=is_downloads_enabled(),
        max_upload_bytes=MAX_UPLOAD_BYTES,
        library_dirs=library_dirs,
    )
