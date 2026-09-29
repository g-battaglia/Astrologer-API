"""Fixed Star Discovery API endpoints."""

from logging import getLogger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import (
    FixedStarDiscoveryFactory,
)
from ..types.request_models import (
    FixedStarDiscoveryRequestModel,
)
from ..types.response_models import (
    FixedStarDiscoveryResponseModel,
)
from ..utils.router_utils import (
    build_subject,
    dump,
    handle_exception,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/fixed-stars/discovery", response_model=FixedStarDiscoveryResponseModel, operation_id="advancedFixedStarDiscovery")
async def fixed_star_discovery(request_body: FixedStarDiscoveryRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/fixed-stars/discovery`

    Discover prominent fixed stars in conjunction with chart points.

    **Parameters:**
    - `subject`: Subject to search for star conjunctions.
    - `orb`: Maximum orb in degrees (default 1.0).

    **Returns:**
    - `stars`: List of prominent fixed stars found.
    """
    log_request_with_body(logger, request, "Fixed star discovery request", request_body.model_dump_json())

    try:
        subject = await run_heavy(build_subject, request_body.subject)
        stars = await run_heavy(
            FixedStarDiscoveryFactory.find_prominent_stars,
            subject,
            orb=request_body.orb,
        )

        return JSONResponse(
            content={
                "status": "OK",
                "stars": dump(stars),
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
