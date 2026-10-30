from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class GenerationRequest:
    kind: str
    messages: list[ChatMessage]
    max_tokens: int = 1200
    timeout: float = 45.0


@dataclass(frozen=True)
class ProviderGenerationResult:
    text: str
    model: str


class LLMProvider(Protocol):
    def generate(self, request: GenerationRequest) -> ProviderGenerationResult:
        """Return application-owned text. Provider SDK types stay inside the adapter."""
