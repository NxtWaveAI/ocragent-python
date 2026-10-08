from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from .._http import HttpClient


class AgentsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        """List all your agents."""
        res = self._http.request("GET", "/agents")
        if isinstance(res, list):
            return res
        return res.get("agents", [])

    def get(self, agent_id: str) -> Dict[str, Any]:
        """Get a single agent with its full extraction schema."""
        return self._http.request("GET", f"/agents/{agent_id}")

    def get_schema(self, agent_id: str) -> Dict[str, Any]:
        """Get just the schema (fields) for an agent."""
        return self._http.request("GET", f"/agents/{agent_id}/schema")

    def update_schema(self, agent_id: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update an agent's extraction schema."""
        return self._http.request("PATCH", f"/agents/{agent_id}/schema", json={"fields": fields})

    def set_status(self, agent_id: str, action: Literal["active", "paused"]) -> None:
        """Pause or reactivate an agent."""
        self._http.request("POST", f"/agents/{agent_id}/status", params={"action": action})

    def delete(self, agent_id: str) -> None:
        """Permanently delete an agent and all its jobs."""
        self._http.request("DELETE", f"/agents/{agent_id}")

    def results(
        self,
        agent_id: str,
        period: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """List extraction results for an agent."""
        return self._http.request(
            "GET",
            f"/agents/{agent_id}/results",
            params={"period": period, "from_date": from_date, "to_date": to_date, "page": page, "limit": limit},
        )

    def export_results(self, agent_id: str, format: Literal["csv", "xlsx"] = "csv") -> bytes:
        """Export all results as CSV or XLSX. Returns raw bytes."""
        return self._http.request(
            "GET",
            f"/agents/{agent_id}/results/export",
            params={"format": format},
            binary=True,
        )

    def stats(self, agent_id: str) -> Dict[str, Any]:
        """Get daily extraction stats (last 7 days)."""
        return self._http.request("GET", f"/agents/{agent_id}/stats")

    def history(self, agent_id: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get extraction history for an agent."""
        return self._http.request(
            "GET", f"/agents/{agent_id}/history", params={"page": page, "limit": limit}
        )

    # ── Agent creation wizard ─────────────────────────────────────

    def create_session(
        self,
        file,
        file_back=None,
        page_layout: Literal["single", "two_sided"] = "single",
        doc_type_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Step 1 — Upload a sample document to start an agent build session.
        Returns ``{"session_id": "..."}`` for subsequent wizard calls.

        :param file: File-like object (open in binary mode). JPEG, PNG, or WEBP.
        :param file_back: Back-page image (only for two_sided layouts).
        :param page_layout: "single" (default) or "two_sided".
        :param doc_type_hint: Optional hint like "invoice" or "passport".

        Example::

            with open("invoice.jpg", "rb") as f:
                session = client.agents.create_session(f, doc_type_hint="invoice")
            session_id = session["session_id"]
        """
        files: Dict[str, Any] = {"file_front": file}
        if file_back:
            files["file_back"] = file_back
        data: Dict[str, Any] = {"page_layout": page_layout}
        if doc_type_hint:
            data["doc_type_hint"] = doc_type_hint
        return self._http.request("POST", "/agents/session", files=files, data=data)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Step 2 — Get AI-generated questions and field suggestions for the session.
        The first call is slow (runs OCR + AI analysis). Subsequent calls are instant.

        Returns a dict with ``questions`` (list) and ``suggested_answers`` (dict).

        Example::

            session = client.agents.get_session(session_id)
            print(session["doc_type_guess"])  # "invoice"
            for q in session["questions"]:
                print(q["key"], "→", q["suggested_value"])
        """
        return self._http.request("GET", f"/agents/session/{session_id}")

    def finalize_session(
        self,
        session_id: str,
        answers: Dict[str, str],
        required_overrides: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """
        Step 3 — Submit answers and create the agent.
        If more info is needed, ``status`` will be ``"needs_more_info"`` and
        ``followup_questions`` will contain the next set of questions.

        Example::

            # Accept all AI suggestions:
            session = client.agents.get_session(session_id)
            answers = {q["key"]: q["suggested_value"] for q in session["questions"]}
            result = client.agents.finalize_session(session_id, answers)
            print(result["agent_id"])  # done!
        """
        body: Dict[str, Any] = {"answers": answers}
        if required_overrides:
            body["required_overrides"] = required_overrides
        return self._http.request("POST", f"/agents/session/{session_id}/answer", json=body)

    def create(
        self,
        file,
        file_back=None,
        page_layout: Literal["single", "two_sided"] = "single",
        doc_type_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method — create an agent in one call by auto-confirming all AI suggestions.
        Returns ``{"agent_id": "...", "agent_name": "..."}`` on success.

        Example::

            with open("invoice.jpg", "rb") as f:
                agent = client.agents.create(f, doc_type_hint="invoice")
            print(agent["agent_id"])
        """
        session = self.create_session(file, file_back=file_back, page_layout=page_layout, doc_type_hint=doc_type_hint)
        session_id = session["session_id"]
        status = self.get_session(session_id)
        answers = {q["key"]: q.get("suggested_value", "") for q in status.get("questions", [])}
        result = self.finalize_session(session_id, answers)
        if result.get("status") != "agent_created" or not result.get("agent_id"):
            followup = "; ".join(q.get("question", "") for q in result.get("followup_questions", []))
            raise RuntimeError(f"Agent creation needs more info: {followup}")
        return {"agent_id": result["agent_id"], "agent_name": result.get("agent_name", "")}
