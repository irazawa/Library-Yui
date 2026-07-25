from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.jobs import load_jobs_from_db
from app.routes.health import router as health_router
from app.routes.jobs import router as jobs_router
from app.routes.library import router as library_router
from app.routes.version import router as version_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Hydrate the in-memory job store from SQLite on startup.

    Best-effort: :func:`load_jobs_from_db` swallows all database errors, so a
    missing/corrupt DB never prevents the API from starting.
    """

    load_jobs_from_db()
    yield


app = FastAPI(title="Library-Yui API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5174", "http://localhost:5174", "http://127.0.0.1:5175", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(library_router)
app.include_router(version_router)
