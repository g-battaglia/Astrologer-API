"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from logging import Logger
from fastapi import Request


def get_write_request_to_log(logger: Logger):
    def write_request_to_log(level, request: Request, message: str | Exception):
        logger.log(level, f"{str(request.url)}: {str(message)}")

    return write_request_to_log
