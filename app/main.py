from contextlib import asynccontextmanager
from typing import Union
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
import app.models  # ensure models are registered with Base
from app.core.exceptions import APIException
from app.routers import (
    auth_router,
    provinces_router,
    districts_router,
    grid_substations_router,
    solar_installations_router,
    generation_readings_router,
    summaries_router,
    users_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Sri Lanka Sustainable Energy Authority (SLSEA) Real-Time Solar Generation Data API.\n\n"
        "Compliant with Richardson Maturity Model Level 2, strict resource-oriented design, "
        "time-series append-only readings, robust RBAC jurisdiction security, and ETag conditional caching."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Location", "ETag"]
)


# ==============================================================================
# Consistent JSON Error Handlers (Unified schema: code, message, context)
# ==============================================================================

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handles domain and operational exceptions with consistent JSON error schema."""
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "code": exc.code,
            "message": exc.message,
            "context": exc.context
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into the consistent JSON error schema."""
    error_details = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        error_details.append({
            "field": field_path,
            "message": err.get("msg"),
            "type": err.get("type")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "The request body or parameters failed validation",
            "context": {"validation_errors": error_details}
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Wraps FastAPI HTTPExceptions into the consistent JSON error schema."""
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "RESOURCE_CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR"
    }
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "code": code_map.get(exc.status_code, "HTTP_ERROR"),
            "message": str(exc.detail),
            "context": {"status_code": exc.status_code}
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unhandled internal server exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred while processing the request",
            "context": {"error_type": exc.__class__.__name__, "detail": str(exc)}
        }
    )


# ==============================================================================
# Include Routers (Strict plural, lowercase, hyphenated nouns)
# ==============================================================================

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(provinces_router, prefix=settings.API_V1_PREFIX)
app.include_router(districts_router, prefix=settings.API_V1_PREFIX)
app.include_router(grid_substations_router, prefix=settings.API_V1_PREFIX)
app.include_router(solar_installations_router, prefix=settings.API_V1_PREFIX)
app.include_router(generation_readings_router, prefix=settings.API_V1_PREFIX)
app.include_router(summaries_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "documentation": f"{settings.API_V1_PREFIX}/docs",
        "endpoints": {
            "tokens": f"{settings.API_V1_PREFIX}/tokens",
            "provinces": f"{settings.API_V1_PREFIX}/provinces",
            "districts": f"{settings.API_V1_PREFIX}/districts",
            "grid_substations": f"{settings.API_V1_PREFIX}/grid-substations",
            "solar_installations": f"{settings.API_V1_PREFIX}/solar-installations",
            "district_generation_summaries": f"{settings.API_V1_PREFIX}/district-generation-summaries"
        }
    }
