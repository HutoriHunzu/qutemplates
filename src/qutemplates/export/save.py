"""Save artifacts from registry to disk."""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from .registry import ArtifactKind, ArtifactRegistry
from .utils import generate_unique_save_name, save_dict, save_fig, time_stamp


def save_all(
    registry: ArtifactRegistry,
    path: str | Path,
    name: str,
    timestamp: str | None = None,
    figures: Figure | list[Figure] | None = None,
) -> Path:
    """Save all artifacts from registry to disk.

    JSON artifacts (data, parameters, etc.) are combined into a single file.
    PY and FIGURE artifacts are saved as separate files.

    Args:
        registry: ArtifactRegistry containing artifacts to save.
        path: Directory path where files should be saved.
        name: Base name for saved files.
        timestamp: Optional timestamp string. Generated if not provided.
        figures: Optional figure(s) to register and save. Convenience parameter
            that registers figures into the registry before saving.

    Returns:
        Path to the saved JSON file.
    """
    if figures is not None:
        figs = [figures] if not isinstance(figures, list) else figures
        for i, fig in enumerate(figs):
            key = "figure" if len(figs) == 1 else f"figure_{i}"
            registry.register(key, fig)

    timestamp = timestamp or time_stamp()
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)

    # Collect all JSON artifacts into one dict
    json_data = {
        key: artifact.payload
        for key, artifact in registry.items()
        if artifact.kind == ArtifactKind.JSON
    }

    # Save combined JSON
    path_iter = generate_unique_save_name(str(directory), name, "data", timestamp, "json")
    json_path = next(path_iter)
    save_dict(json_path, json_data)

    # Save non-JSON artifacts individually
    for key, artifact in registry.items():
        if artifact.kind == ArtifactKind.PY:
            _save_py(artifact.payload, artifact.save_hint or key, directory, name, timestamp)
        elif artifact.kind == ArtifactKind.FIGURE:
            _save_figure(artifact.payload, artifact.save_hint or key, directory, name, timestamp)

    return json_path


def _save_py(content: str, suffix: str, directory: Path, name: str, timestamp: str) -> Path:
    """Save Python code artifact."""
    path_iter = generate_unique_save_name(str(directory), name, suffix, timestamp, "py")
    file_path = next(path_iter)
    file_path.write_text(content)
    return file_path


def _save_figure(fig, suffix: str, directory: Path, name: str, timestamp: str) -> Path:
    """Save matplotlib figure artifact."""
    path_iter = generate_unique_save_name(str(directory), name, suffix, timestamp, "png")
    file_path = next(path_iter)
    save_fig(file_path, fig)
    return file_path



