from __future__ import annotations

from typing import Any, BinaryIO, Dict, List, Optional

from .._http import HttpClient


class ExtractResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def single(
        self,
        agent_id: str,
        file: BinaryIO,
        file_back: Optional[BinaryIO] = None,
        callback_url: Optional[str] = None,
        filename: str = "document",
    ) -> Dict[str, Any]:
        """
        Extract structured data from a single document.
        Returns the result synchronously.

        Usage::

            with open("invoice.pdf", "rb") as f:
                result = client.extract.single(agent_id="...", file=f)
            print(result["data"])
        """
        files: Dict[str, Any] = {"file_front": (filename, file)}
        if file_back:
            files["file_back"] = ("back", file_back)

        data: Dict[str, Any] = {"agent_id": agent_id}
        if callback_url:
            data["callback_url"] = callback_url

        raw = self._http.request("POST", "/extract", data=data, files=files)
        # Normalise: expose "data" as the extracted fields
        raw["data"] = raw.pop("result", {})
        return raw

    def batch(
        self,
        agent_id: str,
        files: List[BinaryIO],
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract from multiple documents at once using the same agent.

        Usage::

            results = client.extract.batch(
                agent_id="...",
                files=[open("a.pdf","rb"), open("b.pdf","rb")],
            )
        """
        # Use a list of tuples so httpx keeps duplicate "files" keys intact.
        # dict() would collapse them, sending only the last file.
        files_param = [("files", (f"file_{i}", f)) for i, f in enumerate(files)]
        data: Dict[str, Any] = {"agent_id": agent_id}
        if callback_url:
            data["callback_url"] = callback_url

        return self._http.request("POST", "/extract/batch", data=data, files=files_param)

    def upload_image(self, file: BinaryIO, filename: str = "image") -> Dict[str, Any]:
        """
        Pre-upload an image and get a URL for use with single().
        Useful for camera captures or async workflows.
        """
        return self._http.request("POST", "/upload/image", files={"file": (filename, file)})
