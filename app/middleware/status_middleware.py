"""
    This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from fastapi import Request, Response
from logging import getLogger
from ..utils.write_response_to_log import get_write_response_to_log


write_response_to_log = get_write_response_to_log(getLogger(__name__))


# https://fastapi.tiangolo.com/tutorial/middleware/
async def add_process_time_header(request: Request, call_next) -> Response:
    response: Response = await call_next(request)
    write_response_to_log(20, request, f"Response status code: {response.status_code}")

    return response
