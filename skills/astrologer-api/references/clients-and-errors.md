# Clients and errors

Use the user's existing HTTP stack when practical. These minimal server-side helpers show the service-specific contract: fixed gateway and host, consumer-key authentication, a timeout, JSON bodies, and explicit response checks. They perform one attempt; retry policy belongs to the application.

Keep `RAPIDAPI_KEY` in server-side environment configuration. The path argument is a suffix such as `/chart/birth-chart`, not a full URL. The examples in [Requests](requests.md) can be passed as the body.

## Python client

Uses the standard library. `AstrologerError` retains structured validation details and `Retry-After` for the caller, without printing the key or request body.

```python
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = "https://astrologer.p.rapidapi.com/api/v6"


class AstrologerError(RuntimeError):
    def __init__(self, status, payload, retry_after=None):
        super().__init__(f"Astrologer request failed (HTTP {status})")
        self.status = status
        self.payload = payload
        self.retry_after = retry_after


def call_astrologer(path, body, *, timeout=30):
    request = Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "X-RapidAPI-Key": os.environ["RAPIDAPI_KEY"],
            "X-RapidAPI-Host": "astrologer.p.rapidapi.com",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        response = error
    with response:
        status = response.status
        retry_after = response.headers.get("Retry-After")
        try:
            payload = json.loads(response.read())
        except (ValueError, UnicodeError):
            payload = {"message": "Non-JSON response"}
    if status != 200 or not isinstance(payload, dict) or payload.get("status") != "OK":
        raise AstrologerError(status, payload, retry_after)
    return payload
```

Call `call_astrologer("/now/subject", {})` for current UTC subject data. Socket/connection errors are intentionally not converted into successful API responses; handle them at the application boundary.

## JavaScript client

For a server runtime with `fetch` and `AbortSignal.timeout`, such as Node.js 20+. Do not ship this function with a real key in browser JavaScript.

```javascript
const BASE_URL = "https://astrologer.p.rapidapi.com/api/v6";

class AstrologerError extends Error {
  constructor(status, payload, retryAfter) {
    super(`Astrologer request failed (HTTP ${status})`);
    this.name = "AstrologerError";
    this.status = status;
    this.payload = payload;
    this.retryAfter = retryAfter;
  }
}

async function callAstrologer(path, body, { timeoutMs = 30000 } = {}) {
  const key = process.env.RAPIDAPI_KEY;
  if (!key) throw new Error("RAPIDAPI_KEY is required");
  const response = await fetch(BASE_URL + path, {
    method: "POST",
    headers: {
      "X-RapidAPI-Key": key,
      "X-RapidAPI-Host": "astrologer.p.rapidapi.com",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(timeoutMs),
    redirect: "error",
  });
  const payload = await response.json().catch(() => ({ message: "Non-JSON response" }));
  if (response.status !== 200 || !payload || payload.status !== "OK") {
    throw new AstrologerError(response.status, payload, response.headers.get("Retry-After"));
  }
  return payload;
}
```

Call `await callAstrologer("/now/subject", {})`. Timeouts and network errors reject the promise; show an actionable failure instead of empty chart data. Never turn a failed request into a cached success.

## Errors and retries

| Failure | Action |
| --- | --- |
| 401 / 403 | Check key, host, subscription and requested version. Do not repeatedly retry unchanged credentials. |
| 404 | Check the full path and catalogue; do not infer that a source-repository route is published on RapidAPI. |
| 422 | Inspect `errors`, especially `loc`, `msg`, `type`. Correct field names, wrapper shape, date/location and unsupported options. |
| 429 | Respect the gateway quota and `Retry-After`; retries may consume more quota. |
| 503 `ServiceInitializing` | Respect `Retry-After`, then make a bounded retry. If still unavailable, report it. |
| 503 `ServerBusy` | Back off and cap attempts; reduce concurrency where appropriate. |
| Other 5xx / non-JSON | Preserve HTTP status and report the service/gateway failure. Do not expose raw HTML as a chart. |
| Timeout / connection failure | Report that completion is unknown. An automatic repeat can repeat billable work. |

`Retry-After` can be seconds or an HTTP date. Bound both attempt count and elapsed time. A small application policy might allow one retry for a transient 503; if the requested delay exceeds the request's time budget, return a retryable error rather than sleeping indefinitely or ignoring the server's delay. Do not retry 422 as though it were a capacity problem.

The service error body can contain `status: "ERROR"`, `message`, `error_type` and/or an `errors` array. Gateway errors may have a different shape. Do not require one error schema before handling the HTTP status, and do not log credentials or full personal request/response bodies.

## Check the integration

- Start with the smallest synthetic payload for the requested feature. Match the exact endpoint and current schema before adding optional fields.
- Confirm HTTP 200, `status: "OK"` and the expected payload. For a chart, check that the SVG is nonempty and renders; for split output check both fields. For XML check nonempty context and the accompanying data object.
- Cover one invalid body (422) and an authentication failure in a mock or controlled test. Verify the client surfaces the error and does not retry it indefinitely.
- If implementing retries, test numeric/date `Retry-After`, the attempt cap and cancellation. Keep these tests mocked; do not intentionally exhaust live quotas.
- Cache only where it fits the requested behavior. Include all computation settings in the key; current-time routes require a deliberate freshness policy and birth data should not enter public shared caches.

Do not treat a passing natal example as proof that every endpoint or combination of options has been tested. Report which requests were checked and which failures were simulated.
