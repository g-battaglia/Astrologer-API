"""
Fixed Stars catalog endpoint.

Exposes the libephemeris fixed-star catalog as a static reference resource,
used by frontends to populate star selectors without duplicating the list
in client code.
"""

from functools import lru_cache
from logging import getLogger

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kerykeion.fixed_stars import FixedStarCatalog

from ..types.response_models import (
    FixedStarMetadataResponseModel,
    FixedStarsCatalogResponseModel,
)
from ..utils.logging_utils import log_request

logger = getLogger(__name__)
router = APIRouter()


@lru_cache(maxsize=1)
def _build_catalog_payload() -> dict:
    """Build and serialize the catalog once; the dumped dict is cached so each
    request just reuses it (the catalog is process-stable)."""
    entries = FixedStarCatalog.list_all()
    return FixedStarsCatalogResponseModel(
        status="OK",
        source="libephemeris",
        count=len(entries),
        stars=[
            FixedStarMetadataResponseModel(
                name=e.name,
                slug=e.slug,
                hip_number=e.hip_number,
                nomenclature=e.nomenclature,
                magnitude=e.magnitude,
            )
            for e in entries
        ],
    ).model_dump()


@router.get(
    "/api/v6/fixed-stars/catalog",
    response_model=FixedStarsCatalogResponseModel,
    response_description="The full libephemeris fixed-star catalog.",
    summary="List all available fixed stars",
)
async def get_fixed_stars_catalog(request: Request) -> JSONResponse:
    """
    **GET** `/api/v6/fixed-stars/catalog`

    Return the full fixed-star catalog from libephemeris. The list is
    process-stable (cached at first call) and identifies every star that
    can be requested via `active_fixed_stars` on any chart endpoint.

    Each entry includes:
    - `name`: IAU canonical name (e.g. `"Vindemiatrix"`, `"Deneb Algedi"`).
    - `slug`: URL/identifier-safe form (spaces → underscores).
    - `hip_number`: Hipparcos catalog id (lookup key).
    - `nomenclature`: Bayer or Flamsteed catalog designation, such as `"alLeo"`.
    - `magnitude`: visual magnitude.
    """
    log_request(logger, request, "Fixed-star catalog list")
    return JSONResponse(content=_build_catalog_payload(), status_code=200)
