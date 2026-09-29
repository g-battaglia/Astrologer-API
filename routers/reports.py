"""Reports API endpoints."""

from logging import getLogger
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from kerykeion import (
    ChartDataFactory,
    CompositeSubjectFactory,
    ReportGenerator,
)
from ..types.request_models import (
    ReportRequestModel,
)
from ..types.response_models import (
    ReportResponseModel,
)
from ..utils.router_utils import (
    build_subject,
    handle_exception,
    run_heavy,
)
from ..utils.logging_utils import log_request_with_body

logger = getLogger(__name__)
router = APIRouter()


@router.post("/api/v6/reports", response_model=ReportResponseModel, operation_id="advancedReport")
async def report(request_body: ReportRequestModel, request: Request) -> JSONResponse:
    """
    **POST** `/api/v6/reports`

    Generate a human-readable text report for an astrological subject.

    **Parameters:**
    - `subject`: Primary subject to generate report for.
    - `second_subject` + `chart_type` ('Synastry'/'Transit'/'Composite'): relational report.
    - `chart_type='Natal'` or `include_aspects=true`: include the aspect table.
    - `include_aspects`, `max_aspects`: aspect-table options.

    **Returns:**
    - `report`: Generated text report string.
    """
    log_request_with_body(logger, request, "Report request", request_body.model_dump_json())

    try:
        kwargs: dict[str, Any] = {}
        if request_body.include_aspects is not None:
            kwargs["include_aspects"] = request_body.include_aspects
        if request_body.max_aspects is not None:
            kwargs["max_aspects"] = request_body.max_aspects

        def _build_report_model():
            primary = build_subject(request_body.subject)
            chart_type = request_body.chart_type
            if chart_type in ("Synastry", "Transit", "Composite"):
                second = build_subject(request_body.second_subject)
                if chart_type == "Composite":
                    composite = CompositeSubjectFactory(primary, second).get_midpoint_composite_subject_model()
                    return ChartDataFactory.create_chart_data("Composite", composite)
                return ChartDataFactory.create_chart_data(chart_type, primary, second)
            # Single-subject: build natal chart data when aspects are wanted so the
            # aspect table is populated; otherwise a bare subject report.
            if chart_type == "Natal" or request_body.include_aspects:
                return ChartDataFactory.create_chart_data("Natal", primary)
            return primary

        model = await run_heavy(_build_report_model)
        generator = ReportGenerator(model)
        report_text = await run_heavy(generator.generate_report, **kwargs)

        return JSONResponse(
            content={
                "status": "OK",
                "report": report_text,
            },
            status_code=200,
        )

    except Exception as exc:  # pragma: no cover
        return await handle_exception(exc, request)
