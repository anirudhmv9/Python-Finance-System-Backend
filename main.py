"""
Finance System API — FastAPI application entrypoint.

Run with: `uvicorn app.main:app --reload`
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, summaries, transactions, users


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Optionally create tables on startup if they are missing (dev convenience).

    For a clean reset, prefer `python seed_db.py` which drops and reseeds.
    """
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description=(
        "REST API for personal finance tracking: transactions, role-based "
        "access (viewer / analyst / admin), and summary analytics backed by SQLite."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "Login and JWT issuance"},
        {"name": "Transactions", "description": "Income and expense CRUD"},
        {"name": "Summaries", "description": "Totals and analyst analytics"},
        {"name": "Users", "description": "Admin user management"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 with structured body for client and OpenAPI clients."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(transactions.router, prefix=settings.api_v1_prefix)
app.include_router(summaries.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
def health() -> dict:
    """Liveness probe (no auth)."""
    return {"status": "ok"}
