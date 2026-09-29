"""Normalize operational settings and emit validated shell assignments.

stdout contains only NAME=value assignments whose values are re-serialized
numbers or members of a closed set. Invalid inputs produce warnings on stderr
and fall back to defaults. Unicode normalization matches the tier validator.
This module uses only the standard library; the entrypoint can handle a missing
interpreter by applying the same defaults.
"""

from __future__ import annotations

import math
import os
import shlex
import sys

from app.utils.ephemeris_readiness import _LEB_TIER_ORDER

#: name -> (default, resolver). Order is the output order, pinned by tests so
#: the eval in the external provisioner stays reviewable against a stable shape.
_TIER_CHOICES = "|".join(_LEB_TIER_ORDER)


def _resolve_tier(name: str, raw: str, default: str, warnings: list[str]) -> str:
    """`.strip().lower()` then the allow-list — the validator's own semantics.

    Normalisation first, so a capital or a stray space is forgiven rather than
    merely diagnosed; the allow-list second, so a typo (`medum`) or an interior
    space (`ba se`) is rejected loudly instead of matching nothing downstream.
    The shell's `tr -d` deleted interior whitespace and would have accepted
    `ba se` as `base`; `.strip()` does not, and rejecting it is the better
    reading — the operator typed something no tier is called.
    """
    normalised = raw.strip().lower()
    if normalised in _LEB_TIER_ORDER:
        return normalised
    warnings.append(f"=== {name}={raw!r} is not one of {_TIER_CHOICES}; using '{default}' ===")
    return default


def _resolve_seconds(
    name: str,
    raw: str,
    default: str,
    minimum: float,
    maximum: float,
    warnings: list[str],
    below_minimum_hint: str = "",
) -> str:
    """A finite number of seconds within [minimum, maximum], canonicalised.

    ``float()`` accepts scientific notation (`1e2`) and the shell's glob did
    not; that is a widening, not a hole — the range check is what protects the
    loop, not the spelling. Two things it accepts DO need their own handling:

    - ``inf`` and ``nan`` parse, and ``nan`` compares false against every
      bound, so finiteness is tested explicitly.
    - Python's numeric grammar is *wider than C's*: Unicode decimal digits
      (``٣``, ``５``) and PEP-515 underscores (``0_5``) all parse here and are
      all rejected by ``sleep``, whose parser is ``strtod``. The first version
      of this function returned the accepted input raw, which meant a value
      could be validated in one grammar and executed in another — ``sleep ٣``
      failing on every poll iteration is a hot loop, which is the exact
      incident class this module exists to end. So the accepted value is
      re-serialised: ``repr(float)`` is always ASCII — plain decimal in these
      ranges, e-notation below 1e-4 (reachable only for the retry delay, whose
      minimum is zero) — and both shapes sit inside ``strtod``'s grammar,
      verified against GNU and BSD ``sleep``. ``-0.0`` is folded to ``0.0`` first, since
      it passes a ``>= 0`` bound and would otherwise emit ``-0.0`` — which
      ``sleep`` reads as an option.
    """
    try:
        value = float(raw)
    except ValueError:
        warnings.append(f"=== {name}={raw!r} is not a plain number of seconds; using {default}s ===")
        return repr(float(default))
    if not math.isfinite(value):
        warnings.append(f"=== {name}={raw!r} is not a plain number of seconds; using {default}s ===")
        return repr(float(default))
    if value < minimum:
        # Stated as the bound, not as a prediction: an earlier wording said a
        # below-minimum value "would spin", which is true of 0 and false of -1
        # (`sleep -1` is an illegal option, not a loop) — a diagnosis about the
        # wrong failure, in the series that keeps deleting those.
        warnings.append(f"=== {name}={raw!r} is below the {minimum}s minimum; using {default}s{below_minimum_hint} ===")
        return repr(float(default))
    if value > maximum:
        warnings.append(f"=== {name}={raw!r} is implausibly long (maximum {maximum}s); using {default}s ===")
        return repr(float(default))
    if value == 0:
        value = 0.0
    return repr(value)


def _resolve_count(
    name: str,
    raw: str,
    default: str,
    maximum: int,
    warnings: list[str],
    *,
    minimum: int = 0,
) -> str:
    """A bounded integer, or the default.

    ``int()`` parses `08` as eight — base ten, no octal trap — and raises on
    anything else, including the 2**63-and-up strings whose only shell-side
    behaviour was to wrap or to error inside `[ -lt ]` with a misleading
    diagnosis about the ephemeris volume.
    """
    try:
        value = int(raw.strip())
    except ValueError:
        warnings.append(f"=== {name}={raw!r} is not a small integer; using {default} ===")
        return default
    if value < minimum or value > maximum:
        warnings.append(f"=== {name}={raw!r} is not a small integer ({minimum}..{maximum}); using {default} ===")
        return default
    return str(value)


def resolve(environ: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Resolve every policy value from *environ*. Pure, so the tests are too."""
    warnings: list[str] = []
    values = {
        "EPHEMERIS_REQUIRED_TIER": _resolve_tier("EPHEMERIS_REQUIRED_TIER", environ.get("EPHEMERIS_REQUIRED_TIER", "base"), "base", warnings),
        "EPHEMERIS_TARGET_TIER": _resolve_tier("EPHEMERIS_TARGET_TIER", environ.get("EPHEMERIS_TARGET_TIER", "extended"), "extended", warnings),
        "WORKER_CYCLE_POLL_S": _resolve_seconds(
            "WORKER_CYCLE_POLL_S",
            environ.get("WORKER_CYCLE_POLL_S", "5"),
            "5",
            minimum=0.05,
            maximum=999,
            warnings=warnings,
            # The one operator-facing place the off-switch is documented; a
            # comment in the external provisioner relies on this hint existing.
            below_minimum_hint=". To disable worker cycling set WORKER_CYCLE_BUDGET=0",
        ),
        "WORKER_CYCLE_BUDGET": _resolve_count("WORKER_CYCLE_BUDGET", environ.get("WORKER_CYCLE_BUDGET", "1"), "1", maximum=99, warnings=warnings),
        "EPHEMERIS_BACKFILL_RETRY_DELAY_S": _resolve_seconds(
            "EPHEMERIS_BACKFILL_RETRY_DELAY_S",
            environ.get("EPHEMERIS_BACKFILL_RETRY_DELAY_S", "60"),
            "60",
            # Zero stays legal here and is rejected for the poll, deliberately:
            # no delay between retries ends when the download succeeds, a zero
            # poll interval never ends. The distinction three shell comments
            # tried to draw is one number here.
            minimum=0,
            maximum=9999,
            warnings=warnings,
        ),
        "EPHEMERIS_GATE_RETRY_DELAY_S": _resolve_seconds(
            "EPHEMERIS_GATE_RETRY_DELAY_S",
            environ.get("EPHEMERIS_GATE_RETRY_DELAY_S", "30"),
            "30",
            minimum=1,
            maximum=999,
            warnings=warnings,
        ),
        "EPHEMERIS_GATE_RETRY_MAX_S": _resolve_seconds(
            "EPHEMERIS_GATE_RETRY_MAX_S",
            environ.get("EPHEMERIS_GATE_RETRY_MAX_S", "300"),
            "300",
            minimum=1,
            maximum=3600,
            warnings=warnings,
        ),
        "HEAVY_MAX_WORKERS": _resolve_count(
            "HEAVY_MAX_WORKERS", environ.get("HEAVY_MAX_WORKERS", "2"), "2", maximum=32, minimum=1, warnings=warnings
        ),
        "HEAVY_MAX_QUEUED": _resolve_count(
            "HEAVY_MAX_QUEUED", environ.get("HEAVY_MAX_QUEUED", "8"), "8", maximum=256, warnings=warnings
        ),
        "HEAVY_QUEUE_TIMEOUT_S": _resolve_seconds(
            "HEAVY_QUEUE_TIMEOUT_S",
            environ.get("HEAVY_QUEUE_TIMEOUT_S", "2"),
            "2",
            minimum=0.05,
            maximum=120,
            warnings=warnings,
        ),
        "NATIVE_SEARCH_MAX_PROCS": _resolve_count(
            "NATIVE_SEARCH_MAX_PROCS",
            environ.get("NATIVE_SEARCH_MAX_PROCS", "1"),
            "1",
            maximum=8,
            minimum=1,
            warnings=warnings,
        ),
        "NATIVE_SEARCH_MAX_QUEUED": _resolve_count(
            "NATIVE_SEARCH_MAX_QUEUED",
            environ.get("NATIVE_SEARCH_MAX_QUEUED", "1"),
            "1",
            maximum=32,
            warnings=warnings,
        ),
        "NATIVE_SEARCH_QUEUE_TIMEOUT_S": _resolve_seconds(
            "NATIVE_SEARCH_QUEUE_TIMEOUT_S",
            environ.get("NATIVE_SEARCH_QUEUE_TIMEOUT_S", "2"),
            "2",
            minimum=0.05,
            maximum=120,
            warnings=warnings,
        ),
    }
    return values, warnings


def main() -> int:
    values, warnings = resolve(dict(os.environ))
    for warning in warnings:
        print(warning, file=sys.stderr)
    for name, value in values.items():
        print(f"{name}={shlex.quote(value)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
