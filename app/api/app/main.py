"""Entry point. Run with: uv run uvicorn app.main:app --reload

API docs (try requests in the browser): http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, crb, health, orders, products, stats, uploads
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.services import crb_refresh

API_PREFIX = "/api/v1"

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Keeps the CRB page's match data up to date while the API is running
    stop = crb_refresh.start() if settings.football_refresh else None
    yield
    if stop is not None:
        stop.set()


app = FastAPI(
    title="CRB Store API",
    lifespan=lifespan,
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url="/docs",
)

# Browsers only let pages from these origins call the API (the Vite proxy in
# development doesn't need it, but a frontend on another domain in production does)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

register_error_handlers(app)

api = APIRouter(prefix=API_PREFIX)
api.include_router(health.router)
api.include_router(auth.router)
api.include_router(products.router)
api.include_router(products.admin_router)
api.include_router(uploads.router)
api.include_router(orders.router)
api.include_router(orders.admin_router)
api.include_router(stats.router)
api.include_router(crb.router)
api.include_router(crb.admin_router)
app.include_router(api)

# Uploaded product photos. The folder only ever contains files saved by the upload
# route, under random names.
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(f"{API_PREFIX}/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
