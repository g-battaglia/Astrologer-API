"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import logging
import logging.config

from fastapi import FastAPI

from .routers import main_router
from .config.settings import settings
from .middleware.secret_key_checker_middleware import SecretKeyCheckerMiddleware


logging.config.dictConfig(settings.LOGGING_CONFIG)
app = FastAPI(
    debug=settings.debug,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    title="Astrologer API",
    version="4.0.0",
    summary="Astrology Made Easy",
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

#------------------------------------------------------------------------------
# Routers 
#------------------------------------------------------------------------------

app.include_router(main_router.router, tags=["Endpoints"])

#------------------------------------------------------------------------------
# Middleware 
#------------------------------------------------------------------------------

if settings.debug is True:
    pass

else:
    app.add_middleware(
        SecretKeyCheckerMiddleware,
        secret_key_name=settings.secret_key_name,
        secret_keys=[
            settings.rapid_api_secret_key,
        ],
    )
