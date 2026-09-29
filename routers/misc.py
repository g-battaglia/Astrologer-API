"""
Miscellaneous endpoints.

Health check and status probes only.
"""

from logging import getLogger

import anyio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config.settings import settings
from ..types.response_models import ApiStatusResponseModel, ProbeResponseModel
from ..utils.logging_utils import log_request

logger = getLogger(__name__)
router = APIRouter()


def _ephemeris_status() -> dict:
    """Return the manifest-backed runtime inventory used by the request gate."""
    from ..utils.ephemeris_readiness import get_ephemeris_status

    return get_ephemeris_status()


def _cached_ephemeris_status() -> dict:
    """Return the cached readiness view; liveness must never trigger validation."""
    from ..utils.ephemeris_readiness import get_cached_ephemeris_status

    return get_cached_ephemeris_status()


def _kerykeion_version() -> str:
    from importlib.metadata import version as pkg_version

    try:
        return pkg_version("kerykeion")
    except Exception:
        return "unknown"


def _public_ephemeris_status(status: dict) -> dict:
    """Expose probe-safe state without internal paths or exception text."""
    state = str(status.get("state") or "unknown")
    if bool(status.get("ready")):
        reason = "ready"
    elif state in {"pending", "initializing", "validating"}:
        reason = "provisioning"
    else:
        reason = "runtime_validation_failed"
    return {
        "ready": bool(status.get("ready")),
        "state": state,
        "reason": reason,
        "precision_tier": status.get("precision_tier"),
    }


def _probe_response(status: dict, *, gate: bool) -> JSONResponse:
    """Shared probe body for ``/health`` and ``/ready``.

    ``gate=True`` turns a not-ready runtime into a 503 with Retry-After;
    ``gate=False`` always answers 200 (pure liveness).
    """
    public_ephemeris = _public_ephemeris_status(status)
    initializing = gate and not public_ephemeris["ready"]
    return JSONResponse(
        content={
            "status": "INITIALIZING" if initializing else "OK",
            "kerykeion_version": _kerykeion_version(),
            "ephemeris_ready": public_ephemeris["ready"],
            "ephemeris": public_ephemeris,
        },
        status_code=503 if initializing else 200,
        headers={"Retry-After": "30"} if initializing else {},
    )


@router.get(
    "/health",
    response_description="Health check",
    response_model=ProbeResponseModel,
    openapi_extra={"security": []},
)
async def health() -> JSONResponse:
    """
    **GET** `/health`

    Public liveness probe for load balancers and monitoring.
    This endpoint is excluded from authentication.

    Pure liveness: it never triggers runtime validation (which can stat and
    re-hash the sealed inventory) — it reports the cached readiness view and
    always answers 200 while the process is alive. ``/ready`` is the probe
    that drives validation.

    **Returns:**
    - `status`: "OK"
    - `kerykeion_version`: installed kerykeion version
    - `ephemeris_ready`: compatibility boolean from the cached readiness view
    - `ephemeris`: sanitized readiness state and reason code
    """
    return _probe_response(_cached_ephemeris_status(), gate=False)


@router.get(
    "/ready",
    response_description="Dependency readiness check",
    response_model=ProbeResponseModel,
    responses={
        503: {
            "description": "Ephemeris runtime is not ready; retry after the delay in the `Retry-After` header.",
            "model": ProbeResponseModel,
        }
    },
    openapi_extra={"security": []},
)
async def ready() -> JSONResponse:
    """Operator readiness probe; calculation routes use the same gate.

    This is the probe allowed to trigger runtime validation (off the event
    loop); a short negative-TTL cache in the readiness module bounds how
    often a failing runtime is revalidated.
    """
    ephemeris = await anyio.to_thread.run_sync(_ephemeris_status)
    return _probe_response(ephemeris, gate=True)


@router.get(
    "/",
    response_description="Status of the API",
    include_in_schema=False,
    response_model=ApiStatusResponseModel,
)
async def status(request: Request) -> JSONResponse:
    """
    **GET** `/`

    Returns basic API status and environment information. Not included in the public schema.

    **Returns:**
    - `status`: "OK"
    - `environment`: deployment environment name
    - `debug`: whether debug mode is enabled
    """
    log_request(logger, request, "API status check")
    response_dict = {
        "status": "OK",
        "environment": settings.env_type,
        "debug": settings.debug,
    }
    return JSONResponse(content=response_dict, status_code=200)
