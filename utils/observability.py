"""Structured operational events with explicitly selected fields.

Application logs complement edge access logs; they do not duplicate latency or
request accounting. Only catalog messages and explicitly validated fields reach
console/notification sinks, including when a dependency writes a legacy record.
"""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
import json
import logging
import os
import re
import sys
from uuid import UUID

CATALOG = {
    "legacy.event": "Legacy log event; inspect the source reference",
    "engine.starting": "Engine startup configuration detected",
    "engine.ready": "Engine ready",
    "engine.unavailable": "Engine initialization unavailable",
    "api.request": "Calculation request accepted",
    "api.request.ok": "Request OK",
    "api.request.failed": "Request returned a non-200 status",
    "api.exception": "Unhandled calculation failure",
    "api.validation": "Request arguments rejected",
    "api.authentication": "Authentication rejected",
    "api.capacity": "Calculation capacity temporarily unavailable",
    "api.source": "Ephemeris source unavailable",
    "notification.test": "Operational notification delivery test (synthetic)",
}
_LEVELS = {logging.DEBUG: "debug", logging.INFO: "info", logging.WARNING: "warn", logging.ERROR: "error", logging.CRITICAL: "error"}
_ENUMS = {
    "outcome": {"success", "unavailable", "invalid_arguments", "forbidden", "busy", "initializing", "degraded", "unknown"},
    "availability_impact": {"none", "unavailable", "degraded", "unknown"},
    "fault": {"internal", "timeout", "connection", "validation", "resource", "source", "unknown"},
    "exception_type": {"RuntimeError", "TypeError", "ValueError", "TimeoutError", "MemoryError", "OSError", "Exception"},
    "error_code": {"date_range", "dst_transition", "resource_limit", "engine_capability", "geonames", "request_validation", "ephemeris_source", "capacity", "internal", "unknown"},
    "backend": {"libephemeris", "swisseph", "unknown"},
    "precision_tier": {"base", "medium", "extended", "unknown"},
    "expected_tier": {"base", "medium", "extended", "unknown"},
}
_ROUTES: dict[str, str] = {}


def register_routes(routes) -> None:
    """Snapshot framework-owned REST templates, never the requested raw path."""
    for route in routes:
        path = getattr(route, "path", None)
        if type(path) is str and path.startswith("/api/v6/") and "/mcp" not in path:
            operation = getattr(route, "unique_id", None) or getattr(route, "name", "unknown")
            if type(operation) is str and re.fullmatch(r"[A-Za-z0-9_]{1,160}", operation):
                _ROUTES[path] = operation


def request_fields(request) -> dict:
    """Return only matched route metadata; unmatched input is not a template."""
    template = getattr(request.scope.get("route"), "path", None)
    if type(template) is str and template in _ROUTES:
        return {"route": template, "operation": _ROUTES[template]}
    return {"route": "unmatched", "operation": "unknown"}


def _revision(value: object) -> str:
    return value if type(value) is str and re.fullmatch(r"[0-9a-f]{40,64}", value) else "unknown"


def _identifier(value: str | None) -> str:
    try:
        return str(UUID(value)) if value else "unknown"
    except (ValueError, AttributeError):
        return "unknown"


@lru_cache(maxsize=1)
def metadata() -> tuple[tuple[str, str], ...]:
    """Read deployment identity once; do not mistake a deploy ID for a version."""
    role = os.getenv("OBSERVABILITY_ROLE", "unknown")
    environment = os.getenv("ENV_TYPE", "unknown")
    fields = {
        "service": "astrologer-api",
        "deployment_role": role if role in {"marketplace", "proxy", "standalone"} else "unknown",
        "environment": environment if environment in {"production", "test", "dev"} else "unknown",
        "git_commit": _revision(os.getenv("RAILWAY_GIT_COMMIT_SHA")),
        "image_revision": _revision(os.getenv("ASTROLOGER_IMAGE_REVISION")),
        "deployment_id": _identifier(os.getenv("RAILWAY_DEPLOYMENT_ID")),
        "replica_id": _identifier(os.getenv("RAILWAY_REPLICA_ID")),
    }
    for distribution in ("kerykeion", "libephemeris"):
        try:
            installed = version(distribution)
        except PackageNotFoundError:
            installed = "unknown"
        fields[f"{distribution}_version"] = installed if re.fullmatch(r"[A-Za-z0-9.+-]{1,64}", installed) else "unknown"
    return tuple(fields.items())


def _clean_field(key: str, value: object):
    if key in _ENUMS:
        return value if type(value) is str and value in _ENUMS[key] else "unknown"
    if key == "route":
        return value if type(value) is str and value in _ROUTES else "unmatched"
    if key == "operation":
        return value if type(value) is str and value in _ROUTES.values() else "unknown"
    if key == "request_id":
        return value if type(value) is str and re.fullmatch(r"[0-9a-f]{32}", value) else None
    if key in {"count", "issue_count"}:
        return value if type(value) is int and 0 <= value <= 1_000_000_000 else None
    if key == "http_status":
        return value if type(value) is int and 100 <= value <= 599 else None
    return None


@dataclass(frozen=True)
class _Event:
    name: str
    fields: tuple[tuple[str, str | int | bool], ...]


def _logger_name(record: logging.LogRecord) -> str:
    name = record.name
    if name in {"root", "uvicorn", "uvicorn.error", "uvicorn.access", "asyncio"}:
        return name
    # Logger names and extra attributes can otherwise themselves contain data.
    if type(name) is str and name in sys.modules and name.startswith(("app.", "kerykeion.", "libephemeris.")):
        return name
    return "external"


def document(record: logging.LogRecord) -> dict:
    """Do not call getMessage()/str(exception), even on a malformed record."""
    event = getattr(record, "_operational_event", None)
    if type(event) is not _Event or event.name not in CATALOG:
        event = _Event("legacy.event", ())
    logger = _logger_name(record)
    line = record.lineno if type(record.lineno) is int and 0 <= record.lineno <= 1_000_000 else 0
    return {
        "schema_version": 1,
        "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "level": _LEVELS.get(record.levelno, "info"),
        "message": CATALOG[event.name],
        "event": event.name,
        "logger": logger,
        "source": f"{logger}:{line}",
        **dict(metadata()),
        **dict(event.fields),
    }


class EventFormatter(logging.Formatter):
    """Railway JSON in hosted runtimes; equally closed text for local consoles."""

    def __init__(self, pretty: bool = False):
        super().__init__()
        self.pretty = pretty

    def format(self, record: logging.LogRecord) -> str:
        try:
            body = document(record)
            if self.pretty:
                return f"{body['timestamp']} {body['level'].upper()} [{body['logger']}] " + json.dumps(body, ensure_ascii=False, allow_nan=False)
            return json.dumps(body, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        except Exception:
            # A fixed fallback cannot expose logging's Message/Arguments dump.
            return '{"schema_version":1,"level":"error","event":"logging.failed","message":"Operational log formatting failed"}'


class QuietStreamHandler(logging.StreamHandler):
    def handleError(self, record):  # noqa: N802
        # A broken stdout must not print the original record or recurse.
        pass


def emit(
    logger: logging.Logger,
    name: str,
    *,
    level: int = logging.INFO,
    request_body: bytes | None = None,
    request_body_complete: bool = False,
    **fields,
) -> None:
    """Attach failed request bodies to console records only."""
    if type(name) is not str or name not in CATALOG:
        return
    cleaned = tuple((key, safe) for key, value in fields.items() if (safe := _clean_field(key, value)) is not None)
    console_fields = cleaned
    if name == "api.request.failed" and request_body is not None:
        try:
            body = request_body.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            body = b64encode(request_body).decode("ascii")
            encoding = "base64"
        console_fields += (("request_body", body), ("request_body_encoding", encoding), ("request_body_complete", request_body_complete))
    event = _Event(name, console_fields)
    try:
        logger.log(level, CATALOG[name], extra={"_operational_event": event}, stacklevel=2)
    except Exception:
        pass
    # Only designated typed events can notify: never arbitrary legacy logs.
    try:
        from .operational_alerts import offer

        offer(name, {**dict(metadata()), **dict(cleaned)})
    except Exception:
        pass


def engine_event(logger: logging.Logger, name: str, status: dict | None = None, *, backend: str = "unknown") -> None:
    """Report observed inventory readiness, independently of its configured floor."""
    if name == "engine.ready" and (status or {}).get("ready") is not True:
        name = "engine.unavailable"
    observed = (status or {}).get("precision_tier") or "unknown"
    expected = os.getenv("OBSERVABILITY_EXPECTED_TIER", "unknown")
    mismatch = name == "engine.ready" and expected in {"base", "medium", "extended"} and observed != expected
    emit(
        logger,
        name,
        level=logging.ERROR if name == "engine.unavailable" else logging.WARNING if mismatch else logging.INFO,
        precision_tier=observed,
        expected_tier=expected,
        backend=backend,
        outcome="initializing" if name == "engine.starting" else "unavailable" if name == "engine.unavailable" else "degraded" if mismatch else "success",
        availability_impact="unknown" if name == "engine.starting" else "unavailable" if name == "engine.unavailable" else "degraded" if mismatch else "none",
    )
