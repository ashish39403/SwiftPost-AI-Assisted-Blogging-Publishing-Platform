from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str


@dataclass(frozen=True)
class ImageResult:
    url: str
    description: str
    page_url: str


class SearchProvider(Protocol):
    def search(self, query: str, *, limit: int, depth: str = "basic") -> list[SearchResult]:
        """Return normalized search hits. Provider SDK types stay inside the adapter."""

    def search_images(self, query: str, *, limit: int) -> list[ImageResult]:
        """Return live image URLs. Optional on a provider; Composer/editor call it through collect_images."""
