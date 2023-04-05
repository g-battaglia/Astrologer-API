"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""


import logging

from datetime import datetime
from fastapi import FastAPI
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware

from .routers import astrology
from .routers import geonames
from .config.settings import settings
from .middleware.rapidapi_middleware import RapidApiMiddleware
from .middleware.status_middleware import add_process_time_header


logging.basicConfig(
    filename=Path(__file__).parent.parent / f'logs/{datetime.now().strftime("%m-%d-%Y")}.log',
    filemode="a",
    force=True,
    format="[%(asctime)s] %(levelname)4s - %(message)s - Module: %(name)s",
    level=settings.log_level,
)

app = FastAPI(
    debug=settings.debug,
    title=settings.app_name,
    version=settings.version,
    description=settings.description,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)

# Routers #
app.include_router(astrology.router, tags=["Astrology"])
app.include_router(geonames.router, tags=["Geonames"])

# Middleware #
app.add_middleware(BaseHTTPMiddleware, dispatch=add_process_time_header)
# With the decorator function would be:
# app.middleware("http")(add_process_time_header)

if settings.debug is False:
    app.add_middleware(
        RapidApiMiddleware,
        secret_keys=[
            settings.rapid_api_secret_key,
        ],
    )
