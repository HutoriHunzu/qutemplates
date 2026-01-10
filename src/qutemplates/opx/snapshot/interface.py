# Snapshot experiment interface for workflow construction

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from matplotlib.artist import Artist
from matplotlib.figure import Figure

from ..handler import OPXContext
from ..tools import AveragerInterface

T = TypeVar("T")


@dataclass
class LivePlottingInterface:
    """
    Interface for live plotting capabilities.

    Contains all methods and interfaces needed for real-time plotting.
    Only created if user implements both setup_plot and update_plot.
    """

    setup_plot: Callable[[], tuple[Figure, list[Artist]] | None]
    update_plot: Callable[[list[Artist], Any], list[Artist]]
    averager_interface: AveragerInterface | None


@dataclass
class SnapshotInterface(Generic[T]):
    """Interface for snapshot workflow - framework polls fetch_results periodically."""

    fetch_results: Callable[[], T | None]  # Live preview
    post_run: Callable[[T], T]  # Process preview
    experiment_name: str
    opx_context: OPXContext
    averager_interface: AveragerInterface | None = None
    live_plotting: LivePlottingInterface | None = None
