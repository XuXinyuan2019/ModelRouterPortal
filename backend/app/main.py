from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
import app.models  # noqa: F401 — ensure all models are registered before create_all
from app.routes.auth import router as auth_router
from app.routes.models import router as models_router
from app.routes.apikeys import router as apikeys_router
from app.routes.balance import router as balance_router
from app.routes.usage import router as usage_router, dashboard_router
from app.routes.settings import router as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ModelRouter Portal API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(models_router)
app.include_router(apikeys_router)
app.include_router(balance_router)
app.include_router(usage_router)
app.include_router(dashboard_router)
app.include_router(settings_router)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
