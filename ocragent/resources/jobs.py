from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from .._http import HttpClient


class JobsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(
        self,
        status: Optional[Literal["completed", "failed", "processing"]] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """List all jobs across all agents."""
        return self._http.request(
            "GET", "/jobs", params={"status": status, "page": page, "limit": limit}
        )

    def get(self, job_id: str) -> Dict[str, Any]:
        """Get the status and result of a specific job."""
        return self._http.request("GET", f"/jobs/{job_id}")

    def result(self, job_id: str) -> Dict[str, Any]:
        """Get the full extracted result for a completed job."""
        return self._http.request("GET", f"/jobs/{job_id}/result")

    def download(self, job_id: str, format: Literal["json", "csv"] = "json") -> bytes:
        """Download the result for a job as JSON or CSV. Returns raw bytes."""
        return self._http.request(
            "GET", f"/jobs/{job_id}/download", params={"format": format}, binary=True
        )

    def delete(self, job_id: str) -> None:
        """Permanently delete a job and its result."""
        self._http.request("DELETE", f"/jobs/{job_id}")
