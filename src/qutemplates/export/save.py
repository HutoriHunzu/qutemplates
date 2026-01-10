"""Save artifacts from registry to disk."""

from __future__ import annotations

from pathlib import Path

from .registry import Artifact, ArtifactKind, ArtifactRegistry
from .utils import generate_unique_save_name, save_dict, save_fig, time_stamp

EXTENSION_BY_KIND = {
    ArtifactKind.JSON: "json",
    ArtifactKind.PY: "py",
    ArtifactKind.FIGURE: "png",
}


def save_all(
    registry: ArtifactRegistry,
    path: str | Path,
    name: str,
    timestamp: str | None = None,
) -> Path:
    """Save all artifacts from registry to disk.

    Args:
        registry: ArtifactRegistry containing artifacts to save.
        path: Directory path where files should be saved.
        name: Base name for saved files.
        timestamp: Optional timestamp string. Generated if not provided.

    Returns:
        Path to the saved data file (if any), otherwise the directory.
    """
    timestamp = timestamp or time_stamp()
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)

    saved_data_path: Path | None = None

    for key, artifact in registry.items():
        file_path = _save_artifact(artifact, directory, name, key, timestamp)
        if key == "data":
            saved_data_path = file_path

    return saved_data_path or directory


def _save_artifact(
    artifact: Artifact,
    directory: Path,
    name: str,
    key: str,
    timestamp: str,
) -> Path:
    """Save a single artifact to disk based on its kind."""
    suffix = artifact.save_hint or key
    extension = EXTENSION_BY_KIND[artifact.kind]
    path_iter = generate_unique_save_name(str(directory), name, suffix, timestamp, extension)
    file_path = next(path_iter)

    if artifact.kind == ArtifactKind.JSON:
        save_dict(file_path, artifact.payload)
    elif artifact.kind == ArtifactKind.PY:
        file_path.write_text(artifact.payload)
    elif artifact.kind == ArtifactKind.FIGURE:
        save_fig(file_path, artifact.payload)

    return file_path
