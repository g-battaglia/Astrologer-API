"""Temporary v6 aliases for clients migrating to the domain routes.

Keep aliases until consumers have migrated and their rollback window closes.
They share canonical handlers and middleware but stay outside OpenAPI.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute

PREFIX = "/api/v6"

LEGACY_V6_PATHS = {
    # Predictive techniques and returns. Analysis and chart data are distinct.
    "/chart/heliocentric-return": "/returns/heliocentric/chart",
    "/chart-data/heliocentric-return": "/returns/heliocentric/data",
    "/context/heliocentric-return": "/returns/heliocentric/context",
    "/chart/lunar-node-crossing": "/returns/lunar-node-crossing/chart",
    "/chart-data/lunar-node-crossing": "/returns/lunar-node-crossing/data",
    "/context/lunar-node-crossing": "/returns/lunar-node-crossing/context",
    "/advanced/secondary-progressions": "/predictive/secondary-progressions/analysis",
    "/chart/secondary-progressions": "/predictive/secondary-progressions/chart",
    "/chart-data/secondary-progressions": "/predictive/secondary-progressions/data",
    "/context/secondary-progressions": "/predictive/secondary-progressions/context",
    "/advanced/solar-arc-directions": "/predictive/solar-arc-directions/analysis",
    "/chart/solar-arc-directions": "/predictive/solar-arc-directions/chart",
    "/context/solar-arc-directions": "/predictive/solar-arc-directions/context",
    "/advanced/primary-directions": "/predictive/primary-directions/analysis",
    "/context/primary-directions": "/predictive/primary-directions/context",
    # Time-range calculations.
    "/chart-data/transit-batch": "/transits/batch",
    "/advanced/transit-aspect-timeline": "/transits/aspect-timeline",
    "/advanced/transit-daily-aspects": "/transits/daily-aspects",
    "/advanced/ephemeris": "/ephemeris",
    "/advanced/astro-calendar": "/calendar",
    # Events and searches.
    "/advanced/eclipses": "/events/eclipses",
    "/advanced/lunations": "/events/lunations",
    "/advanced/retrograde-stations": "/events/retrograde-stations",
    "/advanced/sign-ingresses": "/events/sign-ingresses",
    "/advanced/mundane-aspects": "/events/mundane-aspects",
    "/advanced/planetary-phenomena": "/events/planetary-phenomena",
    "/advanced/heliacal-events": "/events/heliacal-events",
    "/advanced/occultations": "/events/occultations",
    "/advanced/occultations/global": "/events/occultations/global",
    # Other calculation domains.
    "/advanced/midpoints": "/analysis/midpoints",
    "/context/midpoints": "/analysis/midpoints/context",
    "/advanced/declination-aspects": "/analysis/declination-aspects",
    "/advanced/declination-aspects/dual": "/analysis/declination-aspects/dual",
    "/advanced/planetary-nodes": "/analysis/planetary-nodes",
    "/dominants": "/analysis/dominants",
    "/advanced/zodiacal-releasing": "/traditional/zodiacal-releasing",
    "/advanced/profections": "/traditional/profections",
    "/advanced/firdaria": "/traditional/firdaria",
    "/advanced/horary-indicators": "/traditional/horary-indicators",
    "/advanced/relocated-chart": "/locational/relocated-chart",
    "/advanced/astro-cartography": "/locational/astro-cartography",
    "/advanced/fixed-star-discovery": "/fixed-stars/discovery",
    "/advanced/report": "/reports",
    "/moon-voc": "/moon/void-of-course",
    "/advanced/moon-voc-windows": "/moon/void-of-course/windows",
    "/sun-times": "/sun/times",
    "/planetary-hours": "/sun/planetary-hours",
}


def register_legacy_v6_routes(application: FastAPI) -> None:
    """Register real POST aliases, preserving bodies without HTTP redirects."""
    routes = {
        route.path: route
        for route in application.routes
        if isinstance(route, APIRoute) and "POST" in route.methods
    }
    for previous, current in LEGACY_V6_PATHS.items():
        old_path, new_path = PREFIX + previous, PREFIX + current
        if old_path in routes:
            raise RuntimeError(f"Legacy API path already registered: {old_path}")
        if new_path not in routes:
            raise RuntimeError(f"Missing canonical API path: {new_path}")
        route = routes[new_path]
        application.router.add_api_route(
            old_path,
            route.endpoint,
            methods=["POST"],
            response_model=route.response_model,
            status_code=route.status_code,
            dependencies=route.dependencies,
            response_class=route.response_class,
            response_model_include=route.response_model_include,
            response_model_exclude=route.response_model_exclude,
            response_model_by_alias=route.response_model_by_alias,
            response_model_exclude_unset=route.response_model_exclude_unset,
            response_model_exclude_defaults=route.response_model_exclude_defaults,
            response_model_exclude_none=route.response_model_exclude_none,
            responses=route.responses,
            callbacks=route.callbacks,
            route_class_override=type(route),
            name=f"legacy_{route.name}",
            include_in_schema=False,
        )
