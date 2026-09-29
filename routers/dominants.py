"""
Dominants endpoint.

Thin REST wrapper over kerykeion's :class:`DominantsFactory`: the whole
calculation — the interchangeable "schools" (modern / almuten_figuris /
elemental) behind a Strategy pattern — lives in kerykeion. This handler only
adapts the request, builds the subject and serialises the resulting model.
"""

from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kerykeion import DominantsFactory

from ..types.request_models import DominantsRequestModel
from ..types.response_models import DominantsResponseModel
from ..utils.logging_utils import log_request_with_body
from ..utils.router_utils import build_subject, dump, handle_exception, run_heavy

logger = getLogger(__name__)

router = APIRouter()


@router.post("/api/v6/analysis/dominants", response_model=DominantsResponseModel, operation_id='dominants')
async def dominants(request_body: DominantsRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/analysis/dominants`

    Compute the dominants of a natal chart with the chosen ``strategy`` (``modern`` /
    ``almuten_figuris`` / ``elemental``), via kerykeion's ``DominantsFactory``.

    **Parameters:**
    - `subject`: Birth data of the subject to analyse.
    - `strategy`: Calculation school (default `modern`).
    - `active_points`: Optional subset of points to compute. Applied to the subject too, so a short
      list also narrows what the `modern` / `almuten_figuris` schools see (defaults to the standard
      active points).
    - `distribution_method`: `weighted` (default) or `pure_count` for the element/modality tally.
    - `custom_distribution_weights`: Optional per-point weight overrides for that tally.
    - `include_accidental_dignities`: Almuten Figuris only — add the accidental-dignity layer.
    - `include_score_breakdown`: Include a per-rule audit trail.

    **Returns:** `status` + `dominants` (the `DominantsModel`: ranked planets, signs,
    elements, modalities and houses — plus polarity, hemispheres and quadrants for the
    modern method — with the convenience `dominant_*` winners and the optional
    `score_breakdown`).
    """
    log_request_with_body(logger, request, "Dominants request", request_body.model_dump_json())
    try:
        subject = await run_heavy(build_subject, request_body.subject, active_points=request_body.active_points)
        result = await run_heavy(
            DominantsFactory.from_subject,
            subject,
            strategy=request_body.strategy,
            active_points=request_body.active_points,
            distribution_method=request_body.distribution_method,
            custom_weights=request_body.custom_distribution_weights,
            include_accidental_dignities=request_body.include_accidental_dignities,
            include_score_breakdown=request_body.include_score_breakdown,
        )
        return JSONResponse(content={"status": "OK", "dominants": dump(result)}, status_code=200)
    except Exception as exc:  # pragma: no cover - defensive
        return await handle_exception(exc, request)
