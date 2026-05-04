"""Thin client for the Learning Commons Knowledge Graph REST API.

Wraps `https://api.learningcommons.org/knowledge-graph/v0`. Authenticates via
`x-api-key` header, read from the `LC_API_KEY` environment variable (loaded
from `.env` if `python-dotenv` is installed and `load_dotenv()` has been called
earlier in the process).

This is a skeleton — only the endpoints needed for v0 sampling are implemented.
Extend as the pipeline grows.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

DEFAULT_BASE = "https://api.learningcommons.org/knowledge-graph/v0"


@dataclass
class LCClient:
    """Synchronous client for the LC Knowledge Graph REST API."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE
    timeout: float = 30.0

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("LC_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "LC_API_KEY not set. Put it in .env or export it before constructing LCClient."
            )
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"x-api-key": self.api_key},
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "LCClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        r = self._client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    # ---- frameworks ----------------------------------------------------

    def list_frameworks(
        self,
        *,
        academic_subject: str | None = None,
        jurisdiction: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return all StandardsFramework records, optionally filtered."""
        return self._get(
            "/standards-frameworks",
            academicSubject=academic_subject,
            jurisdiction=jurisdiction,
        )["data"]

    # ---- standards within a framework ---------------------------------

    def standards_in_framework(
        self,
        framework_uuid: str,
    ) -> Iterator[dict[str, Any]]:
        """Yield every academic standard inside a framework, paginated.

        The LC API uses cursor-based pagination: each response carries
        `pagination.nextCursor` and `pagination.hasMore`. Pass the cursor
        back in the next request via `?cursor=`.
        """
        cursor: str | None = None
        while True:
            payload = self._get(
                "/academic-standards",
                standardsFrameworkCaseIdentifierUUID=framework_uuid,
                cursor=cursor,
            )
            for item in payload.get("data", []):
                yield item
            pagination = payload.get("pagination", {})
            if not pagination.get("hasMore", False):
                break
            cursor = pagination.get("nextCursor")
            if not cursor:
                break

    # ---- single standard -----------------------------------------------

    def standard_by_id(self, case_uuid: str) -> dict[str, Any]:
        """Return a single StandardsFrameworkItem by its CASE UUID."""
        return self._get(f"/academic-standards/{case_uuid}")["data"]

    # ---- search -------------------------------------------------------

    def search_standards(
        self,
        *,
        query: str | None = None,
        statement_code: str | None = None,
        academic_subject: str | None = None,
        jurisdiction: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic or exact-code search across standards frameworks."""
        return self._get(
            "/academic-standards/search",
            query=query,
            statementCode=statement_code,
            academicSubject=academic_subject,
            jurisdiction=jurisdiction,
        )["data"]


if __name__ == "__main__":
    # Smoke test: list a few math frameworks.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    with LCClient() as client:
        frameworks = client.list_frameworks(academic_subject="Mathematics")
        print(f"{len(frameworks)} math frameworks")
        for f in frameworks[:5]:
            print(f"  - {f.get('name')!r}  [{f.get('jurisdiction')}]")
