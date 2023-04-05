"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""


from logging import Logger
from fastapi import Request


def get_write_response_to_log(logger: Logger):
    def write_response_to_log(level, request: Request, message: str):
        logger.log(level, f"{str(request.url)}: {str(message)}")

    return write_response_to_log
