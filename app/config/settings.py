"""
This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import logging
import pathlib
from logging import getLogger, StreamHandler, INFO
from os import getenv
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

# Open config file
if ENV_TYPE == "production":
    logger.info("Loading production config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.prod.toml", "rb") as config_file:
        config = load_toml(config_file)

elif ENV_TYPE == "test":
    logger.info("Loading test config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.test.toml", "rb") as config_file:
        config = load_toml(config_file)

elif ENV_TYPE == "dev":
    logger.info("Loading development config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.dev.toml", "rb") as config_file:
        config = load_toml(config_file)

else:
    logger.info("No ENV_TYPE set, loading production config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.prod.toml", "rb") as config_file:
        config = load_toml(config_file)


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

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
    debug: bool = config["debug"]
    docs_url: str | None = config["docs_url"]
    redoc_url: str | None = config["redoc_url"]
    secret_key_names: str | list[str] = config.get("secret_key_names", config.get("secret_key_name", ""))

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
                    "handlers": ["access"],
                    "level": level,
                    "propagate": False,
                },
            },
        }


settings = Settings()
