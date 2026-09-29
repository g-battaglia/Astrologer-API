"""
This is part of Astrologer API (C) 2023 Giacomo Battaglia

ASTROLOGER_CONFIG_FILE selects optional TOML defaults; an invalid explicit
path fails at import. Pydantic settings then read environment variables and
ASTROLOGER_ENV_FILE (default .env). Only debug and enable_tracing use the
ASTROLOGER_DEBUG and ASTROLOGER_ENABLE_TRACING aliases; other fields use
their field names as case-insensitive environment names. Environment values
take precedence over dotenv values and TOML defaults. allowed_hosts and
allowed_cors_origins are loaded here but not enforced by the application.
"""

import logging
import pathlib
from logging import getLogger, StreamHandler, INFO
from os import getenv
from pydantic import Field
from pydantic_settings import BaseSettings
from tomllib import load as load_toml
from uvicorn.logging import DefaultFormatter


logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))
logger.addHandler(handler)


def parse_log_level(value: str | int | None, fallback: int = INFO) -> int:
    """Convert log level string/int to Python logging level integer."""
    if value is None:
        return fallback
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        # Try parsing as integer first (e.g., "20")
        if value.isdigit():
            return int(value)
        # Use Python's built-in level name resolution
        level = logging.getLevelName(value.upper())
        return level if isinstance(level, int) else fallback
    return fallback


ENV_TYPE = getenv("ENV_TYPE", False)

# Safe defaults: never search implicitly for external configuration.
config: dict = {
    "admin_email": "admin@example.com",
    "allowed_hosts": [],
    "allowed_cors_origins": [],
    "debug": False,
    "enable_tracing": False,
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "secret_key_names": ["X-API-Key"],
}
config_path = getenv("ASTROLOGER_CONFIG_FILE")
if config_path is not None:
    # An invalid explicit path must stop startup, not switch environments.
    with pathlib.Path(config_path).expanduser().open("rb") as config_file:
        config.update(load_toml(config_file))


class Settings(BaseSettings):
    model_config = {"env_file": getenv("ASTROLOGER_ENV_FILE", ".env"), "env_file_encoding": "utf-8", "extra": "ignore"}

    # Environment variables (loaded from .env file or system environment)
    rapid_api_secret_key: str = ""
    astrologer_studio_secret_key: str = ""
    private_astrologer_api_secret_key: str = ""
    rapid_api_key: str = ""
    env_type: str | bool = ENV_TYPE

    # Log level from environment variable (takes precedence) or TOML config as fallback
    # Accepts: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" or integer values (10, 20, 30, 40, 50)
    log_level: str | int = getenv("LOG_LEVEL", config.get("log_level", "INFO"))

    # Config file
    admin_email: str = config["admin_email"]
    allowed_hosts: list = config["allowed_hosts"]
    allowed_cors_origins: list = config["allowed_cors_origins"]
    # Namespaced env aliases: a bare DEBUG=1 in the deployment environment
    # (common, generic, often set for unrelated tools) would otherwise override
    # the TOML and fail open — debug=True skips SecretKeyCheckerMiddleware and
    # returns tracebacks to clients.
    debug: bool = Field(default=config["debug"], validation_alias="ASTROLOGER_DEBUG")
    enable_tracing: bool = Field(default=config.get("enable_tracing", False), validation_alias="ASTROLOGER_ENABLE_TRACING")
    docs_url: str | None = config["docs_url"]
    redoc_url: str | None = config["redoc_url"]
    secret_key_names: str | list[str] = config.get("secret_key_names", config.get("secret_key_name", ""))
    # Kill-switch for first-class fixed stars on /api/v6/ephemeris.
    # Default ON; flip via TOML or the EPHEMERIS_FIXED_STARS_ENABLED env var
    # (no deploy needed) to reject star-bearing batch requests with a 422.
    ephemeris_fixed_stars_enabled: bool = config.get("ephemeris_fixed_stars_enabled", True)

    @property
    def log_level_int(self) -> int:
        """Return log level as Python logging integer."""
        return parse_log_level(self.log_level)

    @property
    def LOGGING_CONFIG(self) -> dict:
        """Generate logging configuration with current log level."""
        level = self.log_level_int
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "[%(asctime)s] %(levelprefix)s %(message)s - Module: %(name)s",
                    "use_colors": None,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": "[%(asctime)s] %(levelprefix)s %(message)s - Module: %(name)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": level,
                },
                "root": {
                    "handlers": ["default"],
                    "level": level,
                },
                "uvicorn.access": {
                    # Access records include the client address. Route-level
                    # privacy-safe logs replace them with a request ID.
                    "handlers": [],
                    "level": logging.CRITICAL + 1,
                    "propagate": False,
                },
                # Kerykeion DEBUG traces include subject names and calculated
                # positions. Keep dependencies at INFO even when application
                # debugging is enabled; explicit response tracing uses its own
                # middleware and never requires dependency log output.
                "kerykeion": {
                    "level": max(level, logging.INFO),
                    "propagate": True,
                },
                "libephemeris": {
                    "level": max(level, logging.INFO),
                    "propagate": True,
                },
            },
        }


settings = Settings()
