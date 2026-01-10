"""Artifact registry for experiment data collection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any


class ArtifactKind(StrEnum):
    """Types of artifacts that can be saved."""

    JSON = auto()  # dict, list, primitives
    PY = auto()  # Python code/config
    FIGURE = auto()  # matplotlib Figure


@dataclass
class Artifact:
    """Single artifact with payload and metadata."""

    payload: Any
    kind: ArtifactKind
    save_hint: str | None = None


class ArtifactRegistry:
    """Registry for collecting experiment artifacts."""

    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}

    def register(
        self,
        key: str,
        data: Any,
        kind: ArtifactKind | None = None,
        save_hint: str | None = None,
    ) -> None:
        """Register artifact. Kind is inferred if not provided."""
        if key in self._artifacts:
            raise ValueError(f"Key already registered: {key}")

        resolved_kind = kind if kind is not None else self._infer_kind(data)
        self._artifacts[key] = Artifact(payload=data, kind=resolved_kind, save_hint=save_hint)

    def _infer_kind(self, data: Any) -> ArtifactKind:
        """Infer artifact kind from data type."""
        if hasattr(data, "savefig"):
            return ArtifactKind.FIGURE
        if isinstance(data, str) and ("def " in data or "import " in data):
            return ArtifactKind.PY
        return ArtifactKind.JSON

    def get(self, key: str) -> Artifact | None:
        """Get artifact by key."""
        return self._artifacts.get(key)

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._artifacts

    def items(self) -> list[tuple[str, Artifact]]:
        """Return all artifacts as key-value pairs."""
        return list(self._artifacts.items())

    def reset(self) -> None:
        """Clear all artifacts."""
        self._artifacts.clear()
