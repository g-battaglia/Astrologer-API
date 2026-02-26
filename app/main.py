"""
This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import logging
import logging.config

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .routers import misc, charts, data, context, moon_phase
from .config.settings import settings
from .middleware.secret_key_checker_middleware import SecretKeyCheckerMiddleware
from .utils.validation_helpers import format_extra_field_error


logging.config.dictConfig(settings.LOGGING_CONFIG)
app = FastAPI(
    debug=settings.debug,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    title="Astrologer API",
    version="5.0.0",
    summary="Data Driven Astrology",
    description="The Astrologer API is a RESTful service providing extensive astrology calculations, designed for seamless integration into projects. It offers a rich set of astrological charts and data, making it an invaluable tool for both developers and astrology enthusiasts.",
    contact={
        "name": "Kerykeion Astrology",
        "url": "https://www.kerykeion.net/",
        "email": settings.admin_email,
    },
    license_info={
        "name": "AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
)

# ------------------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------------------

app.include_router(charts.router, tags=["Charts"])
app.include_router(data.router, tags=["Chart Data"])
app.include_router(context.router, tags=["AI Context"])
app.include_router(moon_phase.router, tags=["Moon Phase"])
app.include_router(misc.router, tags=["Miscellaneous"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors that provides helpful suggestions
    when users send incorrect field names.
    """
    enriched_errors = []

    for error in exc.errors():
        error_type = error.get("type", "")

        # Check if this is an "extra fields not permitted" error
        if error_type == "extra_forbidden":
            # Get the field name from the location
            location = error.get("loc", [])
            if location:
                field_name = str(location[-1])
                enriched_message = format_extra_field_error(field_name, list(location))
                enriched_errors.append(
                    {
                        "loc": location,
                        "msg": enriched_message,
                        "type": error_type,
                    }
                )
                continue

        # For other errors, sanitize the error to be JSON serializable
        # Remove 'ctx' which may contain non-serializable objects like ValueError
        sanitized_error = {
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "type": error_type,
        }
        enriched_errors.append(sanitized_error)

    logging.warning(f"Validation error on {request.url}: {enriched_errors}")

    return JSONResponse(
        status_code=422,
        content={
            "status": "ERROR",
            "message": "Validation failed",
            "errors": enriched_errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "ERROR", "message": "Internal Server Error"},
    )


# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------

# Secret Key Checker Middleware
if settings.debug is True:
    pass

else:
    app.add_middleware(
        SecretKeyCheckerMiddleware,
        secret_key_names=settings.secret_key_names,
        secret_keys=[
            settings.rapid_api_secret_key,
            settings.astrologer_studio_secret_key,
            settings.private_astrologer_api_secret_key,
            settings.rapid_api_key,
        ],
    )


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
