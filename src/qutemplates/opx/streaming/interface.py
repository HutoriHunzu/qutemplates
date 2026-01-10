# Streaming experiment interface for workflow construction

from collections.abc import Callable
from dataclasses import dataclass
from queue import Queue
from typing import Any, Generic, TypeVar

from matplotlib.artist import Artist
from matplotlib.figure import Figure

from ..handler import AveragerInterface, OPXContext

T = TypeVar("T")


@dataclass
class StreamingInterface(Generic[T]):
    """Interface for streaming workflow - user controls fetch loop via program_coordinator."""

    program_coordinator: Callable[[object, object, Queue], None]  # (job, handles, queue)
    post_run: Callable[[Any], T]  # Process chunks/aggregated data
    setup_plot: Callable[[], tuple[Figure, list[Artist]]]
    update_plot: Callable[[list[Artist], T], list[Artist]]
    experiment_name: str
    opx_context: OPXContext
    averager_interface: AveragerInterface
