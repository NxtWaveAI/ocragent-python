from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from .errors import (
    AgentPausedError,
    AuthError,
    ForbiddenError,
    NotFoundError,
    OcrAgentError,
    PlanLimitError,
    RateLimitError,
    ValidationError,
)

DEFAULT_BASE_URL = "https://apiocr.nxtwaveai.com/v1"
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0


class HttpClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client = httpx.Client(
            timeout=timeout,
            headers={"X-API-Key": api_key},
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        binary: bool = False,
    ) -> Any:
        url = self._base_url + path
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        for attempt in range(1, self._max_retries + 1):
            res = self._client.request(
                method,
                url,
                json=json,
                data=data,
                files=files,
                params=clean_params or None,
            )

            # Retry 429 / 5xx
            if res.status_code == 429 or res.status_code >= 500:
                if attempt < self._max_retries:
                    if res.status_code == 429:
                        # Honour the server's Retry-After header (cap at 60 s).
                        wait = min(int(res.headers.get("Retry-After", 60)), 60)
                    else:
                        # Exponential back-off for transient server errors.
                        wait = min(2 ** (attempt - 1), 30)
                    time.sleep(wait)
                    continue

            if not res.is_success:
                try:
                    err = res.json()
                except Exception:
                    err = {"detail": res.text, "code": "UNKNOWN"}

                msg = err.get("detail", "Unknown error")
                code = err.get("code", "UNKNOWN")

                if res.status_code == 401:
                    raise AuthError(msg)
                if res.status_code == 402:
                    raise PlanLimitError(msg)
                if res.status_code == 403:
                    raise ForbiddenError(msg)
                if res.status_code == 404:
                    raise NotFoundError(msg)
                if res.status_code == 422:
                    if code == "agent_paused":
                        raise AgentPausedError(msg)
                    if code in ("agent_slot_limit", "insufficient_credits", "api_key_credit_limit"):
                        raise PlanLimitError(msg)
                    raise ValidationError(msg)
                if res.status_code == 429:
                    retry_after = int(res.headers.get("Retry-After", 60))
                    raise RateLimitError(retry_after)
                raise OcrAgentError(res.status_code, code, msg)

            if res.status_code == 204:
                return None
            if binary:
                return res.content
            return res.json()

        raise OcrAgentError(0, "MAX_RETRIES", "Max retries exceeded.")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
