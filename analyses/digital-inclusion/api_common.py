"""Small stdlib-only client. Credentials stay in memory and are never logged."""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUTH_PARAMETERS = {"apis.data.go.kr": "serviceKey", "kosis.kr": "apiKey"}


class ApiError(RuntimeError):
    """Safe message only: never include a credential-bearing request URL."""


def load_key(name):
    value = os.environ.get(name)
    if value is None:
        matches = []
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                variable, candidate = line.removeprefix("export ").split("=", 1)
                if variable.strip() == name:
                    candidate = candidate.strip()
                    if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in "\"'":
                        candidate = candidate[1:-1]
                    matches.append(candidate)
        if len(matches) != 1:
            raise ApiError(f"{name}: expected one entry in environment or .env")
        value = matches[0]
    value = value.strip()
    if re.search(r"%[0-9a-fA-F]{2}", value):
        value = urllib.parse.unquote(value)  # Decode once; preserve literal +.
    if len(value) < 16 or any(c.isspace() for c in value):
        raise ApiError(f"{name}: empty or malformed key")
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ApiError("Unexpected redirect; authenticated request stopped")


def _error_code(raw):
    # Only allow short token-shaped API error codes into diagnostics.
    text = raw.decode("utf-8", errors="replace")
    match = re.search(r"<(?:returnReasonCode|resultCode)>([A-Z0-9_-]{1,48})<", text)
    if match:
        return match.group(1)
    match = re.search(r'"(?:resultCode|code|err)"\s*:\s*"?([A-Z0-9_-]{1,48})', text)
    return match.group(1) if match else "unavailable"


def request_json(endpoint, params, key, timeout=60):
    parsed = urllib.parse.urlsplit(endpoint)
    if (parsed.scheme != "https" or parsed.hostname not in AUTH_PARAMETERS
            or parsed.query or parsed.fragment or parsed.username or parsed.password
            or parsed.port not in {None, 443}):
        raise ApiError("Only approved HTTPS API endpoints without query strings are allowed")
    if parsed.hostname == "kosis.kr" and not parsed.path.startswith("/openapi/"):
        raise ApiError("KOSIS credentials are limited to the official OpenAPI path")
    if any(name.lower() in {"servicekey", "apikey"} for name in params):
        raise ApiError("Pass credentials through key, not recorded request parameters")
    query = urllib.parse.urlencode({**params, AUTH_PARAMETERS[parsed.hostname]: key})
    request = urllib.request.Request(endpoint + "?" + query, headers={
        "Accept": "application/json", "User-Agent": "a11y-policy-analysis/1.0",
    })
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        raise ApiError(f"HTTP {exc.code}; API error code: {_error_code(raw)}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ApiError(f"Network failure ({type(exc).__name__}); endpoint and key omitted") from None
    for variant in {key, urllib.parse.quote(key, safe=""), urllib.parse.quote_plus(key)}:
        if variant.encode() in raw:
            raise ApiError("Response contains credential; refused to expose or persist it")
    try:
        return json.loads(raw.decode("utf-8-sig")), raw
    except (ValueError, UnicodeError):
        raise ApiError(f"Expected JSON; API error code: {_error_code(raw)}") from None


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
