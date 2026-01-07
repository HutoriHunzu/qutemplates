# Batch experiment interface for workflow construction

from dataclasses import dataclass
from typing import Callable, TypeVar, Generic

from matplotlib.artist import Artist
from matplotlib.figure import Figure

from ..hardware import OPXContext, AveragerInterface


T = TypeVar('T')


@dataclass
class BatchInterface(Generic[T]):
    """Interface for batch workflow - framework polls fetch_results periodically."""

    fetch_results: Callable[[], T | None]  # Live preview
    post_run: Callable[[T], T]  # Process preview
    setup_plot: Callable[[], tuple[Figure, list[Artist]]]
    update_plot: Callable[[list[Artist], T], list[Artist]]
    experiment_name: str
    opx_context: OPXContext
    averager_interface: AveragerInterface
