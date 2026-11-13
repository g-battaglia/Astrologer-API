"""Optional best-effort alerts, isolated from calculation/request execution.

One bounded daemon sender per worker; no retries, SDK, raw exceptions or logger
callbacks. The external uptime monitor remains necessary when the process dies.
"""

from __future__ import annotations

from collections import Counter, OrderedDict, deque
import json
import os
from queue import Empty, Full, Queue
import re
from threading import Event, Lock, Thread
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

_CAPACITY = 32
_COOLDOWN = 300.0
_WINDOW = 60.0
_GLOBAL_LIMIT = 10
_MAX_KEYS = 2048
_queue: Queue[bytes] = Queue(maxsize=_CAPACITY)
_lock = Lock()
_stop = Event()
_thread: Thread | None = None
_recent: deque[float] = deque()
_last: OrderedDict[tuple[str, str, str], float] = OrderedDict()
_repeated: Counter = Counter()
_counts: Counter = Counter()


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _webhook() -> str | None:
    """Never send an operational secret to an arbitrary URL or proxy."""
    if os.getenv("OBSERVABILITY_ALERTS_ENABLED", "false").lower() != "true":
        return None
    raw = os.getenv("OBSERVABILITY_SLACK_WEBHOOK", "")
    try:
        url = urlsplit(raw)
        if (
            url.scheme == "https"
            and url.hostname == "hooks.slack.com"
            and url.port in (None, 443)
            and not url.username
            and not url.password
            and not url.query
            and not url.fragment
            and re.fullmatch(r"/services/[A-Za-z0-9_-]{1,120}/[A-Za-z0-9_-]{1,120}/[A-Za-z0-9_-]{1,160}", url.path)
        ):
            return raw
    except ValueError:
        pass
    return None


def _deliver(body: bytes, url: str) -> bool:
    # Disable proxy inheritance and redirects; status alone is not Slack's ack.
    opener = build_opener(ProxyHandler({}), _NoRedirects())
    with opener.open(Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=2) as response:
        return response.status == 200 and response.read(32).strip() == b"ok"


def _sender() -> None:
    while not _stop.is_set() or not _queue.empty():
        try:
            body = _queue.get(timeout=0.1)
        except Empty:
            continue
        try:
            url = _webhook()
            delivered = url is not None and _deliver(body, url)
            with _lock:
                _counts["delivered" if delivered else "failed"] += 1
        except Exception:
            # No logger: notification failures must never notify themselves.
            with _lock:
                _counts["failed"] += 1
        finally:
            _queue.task_done()


def offer(name: str, fields: dict) -> bool:
    """Enqueue only designated closed events; do not trust arbitrary callers."""
    global _thread
    if not _webhook() or _stop.is_set():
        return False
    from .observability import CATALOG, _clean_field, metadata

    if name not in {"api.exception", "engine.unavailable", "engine.ready", "notification.test"}:
        return False
    cleaned = {}
    for key in ("operation", "fault", "precision_tier", "expected_tier", "outcome", "availability_impact"):
        if key in fields and (safe := _clean_field(key, fields[key])) is not None:
            cleaned[key] = safe
    if name == "engine.ready" and (cleaned.get("expected_tier") not in {"base", "medium", "extended"} or cleaned.get("precision_tier") == cleaned.get("expected_tier")):
        return False
    fingerprint = (name, cleaned.get("operation", "unknown"), cleaned.get("fault", "unknown"))
    now = time.monotonic()
    with _lock:
        previous = _last.get(fingerprint)
        if previous is not None and now - previous < _COOLDOWN:
            _repeated[fingerprint] = min(_repeated[fingerprint] + 1, 1_000_000_000)
            _counts["suppressed"] += 1
            return False
        while _recent and now - _recent[0] >= _WINDOW:
            _recent.popleft()
        if len(_recent) >= _GLOBAL_LIMIT:
            _counts["dropped"] += 1
            return False
        document = {"event": name, "message": CATALOG[name], **dict(metadata()), **cleaned, "count": min(1 + _repeated.get(fingerprint, 0), 1_000_000_000)}
        body = json.dumps({"text": json.dumps(document, ensure_ascii=False, allow_nan=False)}, ensure_ascii=False).encode()
        try:
            _queue.put_nowait(body)
        except Full:
            _counts["dropped"] += 1
            return False
        _recent.append(now)
        _last[fingerprint] = now
        _last.move_to_end(fingerprint)
        _repeated.pop(fingerprint, None)
        while len(_last) > _MAX_KEYS:
            evicted, _ = _last.popitem(last=False)
            _repeated.pop(evicted, None)
        _counts["queued"] += 1
        if _thread is None or not _thread.is_alive():
            _thread = Thread(target=_sender, name="operational-alerts", daemon=True)
            _thread.start()
    return True


def startup() -> None:
    """Permit a new lifespan without creating a sender before it is needed."""
    with _lock:
        _stop.clear()


def stats() -> dict[str, int]:
    """Technical delivery counters, not durable accounting or a delivery claim."""
    with _lock:
        return {key: _counts[key] for key in ("queued", "delivered", "failed", "dropped", "suppressed")}


def shutdown(timeout: float = 2.0) -> None:
    """A bounded drain; a slow sink never holds application shutdown forever."""
    _stop.set()
    if _thread is not None:
        _thread.join(timeout=max(0.0, min(timeout, 2.0)))
