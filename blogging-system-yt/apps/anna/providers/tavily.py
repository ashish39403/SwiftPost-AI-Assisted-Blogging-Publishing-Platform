import os
import sys
from urllib.parse import urlparse

import httpx
from django.conf import settings

from apps.anna.exceptions import (
    ProviderBudgetExceeded,
    ProviderNotConfigured,
    ProviderUnavailable,
)
from apps.anna.interfaces.search import ImageResult, SearchResult

_TAVILY_URL = "https://api.tavily.com/search"
_live_calls = 0


def _running_django_tests():
    return "test" in sys.argv and os.environ.get("ANNA_LIVE_PROVIDER_TEST") != "1"


class TavilySearchProvider:
    """Tavily adapter. Live calls are blocked during Django tests and capped locally."""

    def search(self, query: str, *, limit: int, depth: str = "basic") -> list[SearchResult]:
        key = settings.TAVILY_API_KEY
        if not key:
            raise ProviderNotConfigured("Search is not configured.")
        if _running_django_tests():
            raise ProviderUnavailable("Live Tavily calls are disabled during automated tests.")

        global _live_calls
        budget = max(0, int(settings.TAVILY_TEST_BUDGET))
        if _live_calls >= budget:
            raise ProviderBudgetExceeded()
        _live_calls += 1

        capped = max(1, min(int(limit or settings.TAVILY_MAX_RESULTS), settings.TAVILY_MAX_RESULTS, 10))
        search_depth = "advanced" if depth == "advanced" else "basic"
        try:
            response = httpx.post(
                _TAVILY_URL,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "query": query.strip(),
                    "max_results": capped,
                    "search_depth": search_depth,
                    "include_answer": False,
                },
                timeout=20.0,
            )
        except httpx.HTTPError as exc:
            raise ProviderUnavailable("Search could not be completed.") from exc

        if response.status_code >= 400:
            raise ProviderUnavailable("Search could not be completed.")

        payload = response.json()
        results = []
        for item in payload.get("results") or []:
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            host = urlparse(url).hostname or ""
            results.append(
                SearchResult(
                    url=url,
                    title=str(item.get("title") or "").strip()[:300],
                    snippet=str(item.get("content") or "").strip()[:800],
                    domain=host.removeprefix("www."),
                )
            )
            if len(results) >= capped:
                break
        return results

    def search_images(self, query: str, *, limit: int) -> list[ImageResult]:
        key = settings.TAVILY_API_KEY
        if not key:
            raise ProviderNotConfigured("Search is not configured.")
        if _running_django_tests():
            raise ProviderUnavailable("Live Tavily calls are disabled during automated tests.")

        global _live_calls
        budget = max(0, int(settings.TAVILY_TEST_BUDGET))
        if _live_calls >= budget:
            raise ProviderBudgetExceeded()
        _live_calls += 1

        capped = max(1, min(int(limit or 6), 6))
        try:
            response = httpx.post(
                _TAVILY_URL,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "query": f"{query.strip()} photograph",
                    "max_results": capped,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_images": True,
                    "include_image_descriptions": True,
                },
                timeout=20.0,
            )
        except httpx.HTTPError as exc:
            raise ProviderUnavailable("Search could not be completed.") from exc

        if response.status_code >= 400:
            raise ProviderUnavailable("Search could not be completed.")

        payload = response.json()
        images = []
        seen = set()
        for item in payload.get("images") or []:
            if isinstance(item, str):
                url = item.strip()
                description = ""
            else:
                url = str((item or {}).get("url") or "").strip()
                description = str((item or {}).get("description") or "").strip()[:300]
            if not url or url in seen:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            seen.add(url)
            images.append(
                ImageResult(
                    url=url[:1000],
                    description=description,
                    page_url="",
                )
            )
            if len(images) >= capped:
                break
        return images
