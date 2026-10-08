"""
OCR Agent Python SDK
====================
Official Python client for the OCR Agent API.

Quick start::

    from ocragent import OcrAgent

    client = OcrAgent(api_key="sk_...")

    # List agents
    agents = client.agents.list()

    # Extract a document
    with open("invoice.pdf", "rb") as f:
        result = client.extract.single(agent_id=agents[0]["id"], file=f)

    print(result["data"])
"""

from ._http import HttpClient as _HttpClient
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
from .resources import AgentsResource, ExtractResource, JobsResource

__all__ = [
    "OcrAgent",
    "OcrAgentError",
    "AuthError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "PlanLimitError",
    "AgentPausedError",
]

__version__ = "1.0.1"


class OcrAgent:
    """
    OCR Agent API client.

    :param api_key: Your API key (starts with ``sk_``). Generate one at
        https://ocr.nxtwaveai.com/settings
    :param base_url: Override the API base URL (default: https://apiocr.nxtwaveai.com/v1)
    :param max_retries: Maximum total attempts on 429 / 5xx (default: 3 — up to 2 retries after the first attempt)
    :param timeout: Request timeout in seconds (default: 30)

    Usage::

        client = OcrAgent(api_key="sk_...")

        # Extract a document
        with open("invoice.pdf", "rb") as f:
            result = client.extract.single(agent_id="...", file=f)
        print(result["data"])
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://apiocr.nxtwaveai.com/v1",
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        if not api_key:
            raise ValueError("OcrAgent: api_key is required.")

        self._http = _HttpClient(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
        )
        self.agents = AgentsResource(self._http)
        self.extract = ExtractResource(self._http)
        self.jobs = JobsResource(self._http)

    def close(self):
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
