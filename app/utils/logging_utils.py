"""
Logging utilities for standardized request logging.

This is part of Astrologer API (C) 2023 Giacomo Battaglia
"""

from fastapi import Request
from logging import Logger


def get_origin_domain(request: Request) -> str:
    """
    Extract origin domain from request headers.

    Checks headers in order: Origin, Referer, Host.

    Args:
        request: FastAPI Request object

    Returns:
        Origin domain or "unknown" if not determinable
    """
    from urllib.parse import urlparse

    # Check Origin header first (CORS requests)
    origin = request.headers.get("Origin")
    if origin:
        return origin

    # Fallback: extract domain from Referer header
    referer = request.headers.get("Referer")
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    # Fallback: Host header
    host = request.headers.get("Host")
    if host:
        return host

    return "unknown"


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request, considering proxy headers.

    Checks X-Forwarded-For and X-Real-IP headers for proxied requests,
    falls back to direct client host.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as string, or "unknown" if not determinable
    """
    # Check X-Forwarded-For header (may contain comma-separated list)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP in the list is the original client
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client connection
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def log_request(logger: Logger, request: Request, description: str) -> None:
    """
    Log request with standardized format at INFO and DEBUG levels.

    INFO level logs: METHOD path | IP: x.x.x.x | description
    DEBUG level logs: Request body as JSON

    Args:
        logger: Logger instance to use
        request: FastAPI Request object
        description: Human-readable description of the endpoint action
    """
    client_ip = get_client_ip(request)
    origin = get_origin_domain(request)
    logger.info(f"{request.method} {request.url.path} | IP: {client_ip} | Origin: {origin} | {description}")


def log_request_with_body(logger: Logger, request: Request, description: str, body_json: str) -> None:
    """
    Log request with standardized format at INFO and DEBUG levels, including body.

    INFO level logs: METHOD path | IP: x.x.x.x | description
    DEBUG level logs: Request body as JSON

    Args:
        logger: Logger instance to use
        request: FastAPI Request object
        description: Human-readable description of the endpoint action
        body_json: JSON string of the request body (from model_dump_json())
    """
    client_ip = get_client_ip(request)
    origin = get_origin_domain(request)
    logger.info(f"{request.method} {request.url.path} | IP: {client_ip} | Origin: {origin} | {description}")
    logger.debug(f"Request body: {body_json}")
