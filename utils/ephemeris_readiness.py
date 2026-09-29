"""Manifest-backed readiness for a sealed ephemeris runtime.

An external provisioner installs and validates the LEB2 groups and IERS cache,
then publishes ``.initialized`` atomically. Workers revalidate the reader,
inventory, network policy, and catalog; the marker alone is not sufficient.
Positive cache entries follow marker identity, while negative entries use a
short TTL. Liveness probes only read the cached view.
"""

from __future__ import annotations

import functools
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any


_READY_MARKER = ".initialized"
_REQUIRED_TIER_ENV = "EPHEMERIS_REQUIRED_TIER"

# Post-3.1.0 canonical four groups: the last-resort answer when neither the
# library nor its metadata can be consulted. Under-demanding is the safe
# direction — "the worst case of a wrong present is a repair download that
# does not happen" — and the gate still validates the full live set.
_FALLBACK_LEB_GROUPS = ("core", "asteroids", "exotics", "apogee")
_LEB_TIER_ORDER = ("base", "medium", "extended")


@functools.lru_cache(maxsize=1)
def _probe_leb_groups() -> tuple[str, ...]:
    """Stdlib-only group set for the filesystem probe, version-aware.

    ``probe_tier_present`` must not pay to import libephemeris, but a frozen
    set desyncs across the 3.1.0 uranians retirement: on a locked 3.0.x an
    interrupted backfill missing only ``{tier}_uranians.leb2`` would probe as
    complete and skip the repair download. ``importlib.metadata`` reads the
    installed distribution's version without importing the package, so the
    probe demands the set the installed downloader actually installs. Any
    surprise (missing distribution, unparseable version) falls back to the
    post-3.1.0 four groups.
    """
    try:
        from importlib.metadata import version

        major, minor = (int(part) for part in version("libephemeris").split(".")[:2])
        if (major, minor) < (3, 1):
            return (*_FALLBACK_LEB_GROUPS, "uranians")
    except Exception:  # noqa: BLE001 — any metadata failure means "fall back"
        pass
    return _FALLBACK_LEB_GROUPS


@functools.lru_cache(maxsize=1)
def _required_leb_groups() -> tuple[str, ...]:
    """Canonical LEB2 distribution groups, read from libephemeris itself.

    The gate must demand exactly what `libephemeris download leb2-<tier>`
    installs. Hardcoding the list desyncs on library upgrades: 3.1.0 retired
    the ``uranians`` companion, and a frozen five-group list here would have
    503-gated every deploy forever while the volume was actually complete.

    Deliberately lazy: importing libephemeris at module import time would
    break the stdlib-only contracts of ``probe_tier_present`` and
    ``startup_env`` and crash-loop the API worker on a broken install
    instead of letting it start degraded. On any import failure the static
    fallback answers.
    """
    try:
        from libephemeris.leb_groups import LEB2_GROUPS
    except Exception:  # noqa: BLE001 — any import-time failure means "fall back"
        return _probe_leb_groups()
    return tuple(LEB2_GROUPS)

# A failed validation may be a transient filesystem or parse hiccup, so it must
# be allowed to heal — but re-validating on every poll would let /ready and the
# calculation gate re-open (and re-hash) the inventory in a request storm.
# Cache the negative report for a short TTL instead.
_NEGATIVE_STATUS_TTL_S = 10.0
_monotonic = time.monotonic

_cache_lock = threading.Lock()
_cached_marker_signature: tuple[int, int] | None = None
_cached_status: dict[str, Any] | None = None
_cached_negative_signature: tuple[int, int] | None = None
_cached_negative_status: dict[str, Any] | None = None
_cached_negative_expires_at: float | None = None
# Latched once a positive validation is cached; read without the lock by the
# per-request fast paths (a bool read is atomic). Not monotonic: a marker
# re-publish whose revalidation fails clears it again, so readers must
# tolerate a True -> False transition and never use it to gate one-shot
# initialization.
_ready_latched = False


def _managed_data_dir() -> Path | None:
    value = os.environ.get("LIBEPHEMERIS_DATA_DIR")
    return Path(value) if value else None


def _required_tier() -> str:
    return os.environ.get(_REQUIRED_TIER_ENV, "extended").strip().lower()


def _eligible_tiers(tier: str) -> tuple[str, ...]:
    """Return every tier eligible for best-by-date routing through ``tier``."""
    try:
        return _LEB_TIER_ORDER[: _LEB_TIER_ORDER.index(tier) + 1]
    except ValueError as exc:
        raise ValueError(f"Unsupported required ephemeris tier: {tier!r}") from exc


def _expected_leb_files(tier: str, groups: tuple[str, ...] | None = None) -> list[str]:
    resolved = _required_leb_groups() if groups is None else groups
    return [f"{eligible_tier}_{group}.leb2" for eligible_tier in _eligible_tiers(tier) for group in resolved]


def _base_status(**overrides: Any) -> dict[str, Any]:
    """Single builder for the status-dict shape every producer must share."""
    status: dict[str, Any] = {
        "ready": False,
        "managed": True,
        "state": "invalid",
        "mode": None,
        "precision_tier": None,
        "network_policy": None,
        "expected_groups": list(_required_leb_groups()),
        "expected_files": [],
        "groups": [],
        "catalog": [],
        "planet_centers": None,
        "iers": {},
        "warnings": [],
        "errors": [],
    }
    status.update(overrides)
    return status


def _unmanaged_status() -> dict[str, Any]:
    """Lightweight local-development state: nothing is provisioned or gated."""
    return _base_status(
        ready=True,
        managed=False,
        state="local-unmanaged",
        expected_groups=[],
    )


def _unvalidated_status() -> dict[str, Any]:
    """Cached-view placeholder before this worker has evaluated readiness."""
    return _base_status(state="pending", precision_tier=_required_tier())


def _initializing_status(*, marker_present: bool = False) -> dict[str, Any]:
    tier = _required_tier()
    try:
        expected_files = _expected_leb_files(tier)
        tier_errors: list[str] = []
    except ValueError as exc:
        expected_files = []
        tier_errors = [str(exc)]
    if not marker_present:
        tier_errors.append("Provisioning marker is not present.")
    return _base_status(
        state="validating" if marker_present else "initializing",
        precision_tier=tier,
        expected_files=expected_files,
        errors=tier_errors,
    )


def _required_product_catalog(ephe: Any) -> list[tuple[str, int]]:
    """Derive Kerykeion's engine-backed minor-body catalog, without literals."""
    # These two live beside the subject factory, which moved into a package of
    # its own after 6.0.0a83. Neither is on the top-level facade, so the module
    # path is the only way in and both spellings must be accepted while the
    # pinned version and the current source tree disagree.
    try:
        from kerykeion.astrological_subject.factory import STANDARD_PLANETS, TNO_PLANETS
    except ModuleNotFoundError:  # kerykeion <= 6.0.0a83
        from kerykeion.astrological_subject_factory import STANDARD_PLANETS as LEGACY_STANDARD_PLANETS, TNO_PLANETS as LEGACY_TNO_PLANETS

        STANDARD_PLANETS = LEGACY_STANDARD_PLANETS
        TNO_PLANETS = LEGACY_TNO_PLANETS

    candidates = list(STANDARD_PLANETS.items())
    candidates.extend((name, ephe.AST_OFFSET + number) for name, number in TNO_PLANETS.items())
    return [(name, int(body_id)) for name, body_id in candidates if body_id in ephe.SPK_BODY_NAME_MAP]


def validate_ephemeris_runtime() -> dict[str, Any]:
    """Inspect the active runtime and return a machine-readable readiness report."""
    errors: list[str] = []
    warnings: list[str] = []
    tier = _required_tier()
    try:
        expected_files = _expected_leb_files(tier)
    except ValueError as exc:
        expected_files = []
        errors.append(str(exc))
    report = _base_status(
        managed=_managed_data_dir() is not None,
        precision_tier=tier,
        expected_files=expected_files,
        warnings=warnings,
        errors=errors,
    )
    if errors:
        return report

    try:
        import libephemeris as ephe

        inventory = ephe.get_leb_inventory()
        requirements = ephe.get_runtime_data_requirements(tier)
    except Exception as exc:
        errors.append(f"Cannot inspect libephemeris runtime: {exc}")
        return report

    report["mode"] = inventory.get("mode")
    report["precision_tier"] = inventory.get("precision_tier")
    report["network_policy"] = inventory.get("network_policy_effective")
    if report["mode"] != "leb":
        errors.append(f"Calculation mode must be 'leb', got {report['mode']!r}.")
    # The required tier is a FLOOR, not an equality. Tiers are cumulative, so a
    # runtime configured above the gate (e.g. serving 'extended' while the gate
    # only demands 'base') covers strictly more than the contract asks for and
    # must pass. Demanding equality made the gate unsatisfiable the moment the
    # two were deliberately split — the runtime stays at its configured
    # precision while readiness is granted at the smallest serving tier.
    active_tier = report["precision_tier"]
    try:
        tier_is_sufficient = _LEB_TIER_ORDER.index(active_tier) >= _LEB_TIER_ORDER.index(tier)
    except ValueError:
        tier_is_sufficient = False
    if not tier_is_sufficient:
        errors.append(
            f"Precision tier must be at least {tier!r}, got {active_tier!r}."
        )
    if report["network_policy"] != "sealed":
        errors.append(f"Network policy must be 'sealed', got {report['network_policy']!r}.")
    if not inventory.get("ready"):
        errors.append(str(inventory.get("error") or "No active LEB reader."))

    expected_names = set(report["expected_files"])
    expected_leb: dict[str, Any] = {}
    for requirement in requirements:
        if requirement.kind != "leb2":
            continue
        if requirement.name in expected_leb:
            errors.append(f"Duplicate LEB requirement: {requirement.name}.")
            continue
        expected_leb[requirement.name] = requirement

    actual_files = {item.get("name"): item for item in inventory.get("files", [])}
    for name in report["expected_files"]:
        leb_requirement: Any = expected_leb.get(name)
        if leb_requirement is None:
            errors.append(f"The manifest has no reviewed LEB requirement for: {name}.")
            continue
        actual = actual_files.get(leb_requirement.name)
        if actual is None:
            errors.append(f"Required reviewed LEB group is missing: {leb_requirement.name}.")
            continue
        reviewed = bool(actual.get("reviewed"))
        requirement_tier = leb_requirement.name.split("_", 1)[0]
        report["groups"].append(
            {
                "name": leb_requirement.name,
                "tier": requirement_tier,
                "group": leb_requirement.group,
                "reviewed": reviewed,
                "body_count": int(actual.get("body_count", 0)),
            }
        )
        if not reviewed:
            errors.append(f"LEB group does not match the reviewed manifest: {leb_requirement.name}.")

    unexpected_requirements = sorted(set(expected_leb) - expected_names)
    if unexpected_requirements:
        errors.append("The manifest returned unexpected LEB requirements for this tier: " + ", ".join(unexpected_requirements) + ".")

    try:
        catalog = _required_product_catalog(ephe)
        for point_name, body_id in catalog:
            body_coverage = ephe.get_body_coverage(body_id)
            entry = {
                "point_name": point_name,
                "body_id": body_id,
                "reviewed": bool(body_coverage and body_coverage.reviewed),
                "coverage_start_jd": body_coverage.jd_start if body_coverage else None,
                "coverage_end_jd": body_coverage.jd_end if body_coverage else None,
            }
            report["catalog"].append(entry)
            if body_coverage is None:
                errors.append(f"Exposed point has no LEB coverage: {point_name} ({body_id}).")
            elif not body_coverage.reviewed:
                errors.append(f"Exposed point is backed by unreviewed data: {point_name} ({body_id}).")
    except Exception as exc:
        errors.append(f"Cannot validate the exposed point catalog: {exc}")

    try:
        from libephemeris.iers_data import (
            DEFAULT_MAX_AGE_DAYS,
            get_iers_cache_info,
            load_iers_data,
        )

        load_iers_data(force_download=False)
        iers_info = get_iers_cache_info()
        report["iers"] = {
            "finals": bool(iers_info.get("finals_exists")),
            "leap_seconds": bool(iers_info.get("leap_seconds_exists")),
            "delta_t": bool(iers_info.get("delta_t_exists")),
            "finals_age_days": iers_info.get("finals_age_days"),
            "leap_seconds_age_days": iers_info.get("leap_seconds_age_days"),
            "delta_t_age_days": iers_info.get("delta_t_age_days"),
            "data_points": int(iers_info.get("data_points") or 0),
            "leap_second_entries": int(iers_info.get("leap_second_entries") or 0),
            "delta_t_entries": int(iers_info.get("delta_t_entries") or 0),
        }
        missing_iers = [name for name in ("finals", "leap_seconds", "delta_t") if not report["iers"][name]]
        if missing_iers:
            errors.append(f"Required IERS cache entries are missing: {', '.join(missing_iers)}.")
        empty_iers = [name for name in ("data_points", "leap_second_entries", "delta_t_entries") if not report["iers"][name]]
        if empty_iers:
            errors.append(f"Required IERS cache entries could not be parsed: {', '.join(empty_iers)}.")
        stale_iers = [
            name.removesuffix("_age_days")
            for name in ("finals_age_days", "leap_seconds_age_days", "delta_t_age_days")
            if isinstance(report["iers"].get(name), (int, float)) and report["iers"][name] > DEFAULT_MAX_AGE_DAYS
        ]
        if stale_iers:
            warnings.append(f"IERS cache refresh is overdue for: {', '.join(stale_iers)} (>{DEFAULT_MAX_AGE_DAYS} days).")
    except Exception as exc:
        errors.append(f"Cannot inspect IERS cache: {exc}")

    report["ready"] = not errors
    if errors:
        report["state"] = "invalid"
    elif warnings:
        report["state"] = "ready-degraded"
    else:
        report["state"] = "ready"
    return report


def get_ephemeris_status() -> dict[str, Any]:
    """Return cached managed readiness, or a lightweight local-development state."""
    global _cached_marker_signature, _cached_status
    global _cached_negative_signature, _cached_negative_status, _cached_negative_expires_at
    global _ready_latched

    data_dir = _managed_data_dir()
    if data_dir is None:
        return _unmanaged_status()

    marker = data_dir / _READY_MARKER
    try:
        stat = marker.stat()
    except OSError:
        return _initializing_status()
    signature = (stat.st_mtime_ns, stat.st_size)

    with _cache_lock:
        if _cached_marker_signature == signature and _cached_status is not None:
            return _cached_status
        # Positive validation is immutable for this marker/package process and
        # can be latched. A negative report may be a transient filesystem or
        # parse failure; never pin the subscription service to 503 forever just
        # because the marker signature itself did not change — but do not
        # re-run the (potentially hashing) validation on every poll either:
        # serve the cached negative until its short TTL expires.
        if _cached_negative_signature == signature and _cached_negative_status is not None and _cached_negative_expires_at is not None and _monotonic() < _cached_negative_expires_at:
            return _cached_negative_status
        status = validate_ephemeris_runtime()
        if status.get("ready"):
            _cached_marker_signature = signature
            _cached_status = status
            _cached_negative_signature = None
            _cached_negative_status = None
            _cached_negative_expires_at = None
            _ready_latched = True
        else:
            _cached_marker_signature = None
            _cached_status = None
            _ready_latched = False
            _cached_negative_signature = signature
            _cached_negative_status = status
            _cached_negative_expires_at = _monotonic() + _NEGATIVE_STATUS_TTL_S
        return status


def get_cached_ephemeris_status() -> dict[str, Any]:
    """Return the current readiness view without ever triggering validation.

    Liveness probes must not pay for — or serialize behind — runtime
    validation. They report the cached snapshot (even a stale negative one)
    and leave revalidation to ``/ready`` and the calculation gate.
    """
    if _managed_data_dir() is None:
        return _unmanaged_status()
    # Lock-free snapshot reads: the cached dicts are published fully built
    # under _cache_lock and never mutated afterwards, so a plain reference
    # read is safe — while an in-flight validation HOLDS that lock for its
    # entire (potentially inventory-hashing) duration, and taking it here
    # would serialize liveness behind the volume on the event loop.
    status = _cached_status
    if status is not None:
        return status
    negative = _cached_negative_status
    if negative is not None:
        return negative
    return _unvalidated_status()


def is_ephemeris_ready() -> bool:
    """Return whether every sealed-runtime requirement is currently satisfied."""
    return bool(get_ephemeris_status()["ready"])


def is_ephemeris_ready_latched() -> bool:
    """Synchronous per-request fast path: no lock, no stat, no validation.

    True once a positive validation has been latched for this process (the
    sealed inventory is immutable, so the latch only clears via
    :func:`reset_ephemeris_readiness_cache` or a marker change that fails
    revalidation), and in unmanaged local development where nothing is gated.
    """
    return _ready_latched or _managed_data_dir() is None


def reset_ephemeris_readiness_cache() -> None:
    """Clear the marker-keyed cache (test and controlled-reload helper)."""
    global _cached_marker_signature, _cached_status
    global _cached_negative_signature, _cached_negative_status, _cached_negative_expires_at
    global _ready_latched
    with _cache_lock:
        _cached_marker_signature = None
        _cached_status = None
        _cached_negative_signature = None
        _cached_negative_status = None
        _cached_negative_expires_at = None
        _ready_latched = False


def probe_tier_present(tier: str) -> tuple[bool, list[str]]:
    """Report whether every LEB2 file up to *tier* is already on the volume.

    Deliberately stdlib-only, and deliberately *not* a validation: this
    answers the provisioner's filesystem question — "is there anything left to
    download for this tier?" — so it must not pay to import libephemeris or
    build a reader. The full validator answers a different question (may this
    inventory serve traffic?) and remains the only thing that opens the gate.

    A tier reported present is therefore never treated as proven good. The
    worst case of a wrong "present" is a repair download that does not happen;
    a partial artifact still fails when the reader parses it, and the gate
    still withholds calculation traffic.
    """
    data_dir = _managed_data_dir()
    if data_dir is None:
        return True, []
    leb_dir = data_dir / "leb"
    missing = [
        name
        for name in _expected_leb_files(tier, groups=_probe_leb_groups())
        if not (leb_dir / name).is_file()
    ]
    return not missing, missing


def main() -> int:
    """Validate independently of the marker; used by the provisioning process.

    With ``--probe-only`` it answers the cheap presence question instead, for
    the coverage backfill in the external provisioner.
    """
    if "--probe-only" in sys.argv[1:]:
        tier = _required_tier()
        try:
            present, missing = probe_tier_present(tier)
        except ValueError as exc:  # unsupported tier name
            print(json.dumps({"tier": tier, "present": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps({"tier": tier, "present": present, "missing": missing}, sort_keys=True))
        return 0 if present else 1

    report = validate_ephemeris_runtime()
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
