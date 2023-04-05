"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

import pathlib
from logging import getLogger
from os import getenv
from pydantic import BaseSettings
from tomllib import load as load_toml


logger = getLogger(__name__)

ENV_TYPE = getenv("ENV_TYPE", False)
RAPID_API_SECRET_KEY = getenv("RAPID_API_SECRET_KEY", False)
GEONAMES_USERNAME = getenv("GEONAMES_USERNAME", False)

# Open config file
if ENV_TYPE == "production":
    logger.debug("Loading production config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.prod.toml", "rb") as config_file:
        config = load_toml(config_file)

elif ENV_TYPE == "test":
    logger.debug("Loading test config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.test.toml", "rb") as config_file:
        config = load_toml(config_file)

elif ENV_TYPE == "dev":
    logger.debug("Loading development config")
    with open(pathlib.Path(__file__).parent.absolute() / "config.dev.toml", "rb") as config_file:
        config = load_toml(config_file)

else:
    logger.error("No ENV_TYPE set, exiting")
    exit(1)


class Settings(BaseSettings):
    # Environment variables
    rapid_api_secret_key: str = getenv("RAPID_API_SECRET_KEY", "")
    geonames_username: str = getenv("GEONAMES_USERNAME", "")

    # Config file
    admin_email: str = config["admin_email"]
    allowed_hosts: list = config["allowed_hosts"]
    allowed_cors_origins: list = config["allowed_cors_origins"]
    app_name: str = config["app_name"]
    description: str = config["description"]
    debug: bool = config["debug"]
    docs_url: str | None = config["docs_url"]
    redoc_url: str | None = config["redoc_url"]
    version: str = config["version"]
    log_level: int = config["log_level"]


settings = Settings()
