# Streaming experiment interface for workflow construction

from dataclasses import dataclass
from typing import Callable, TypeVar, Generic, Any
from queue import Queue

from matplotlib.artist import Artist
from matplotlib.figure import Figure

from ..hardware import OPXContext, AveragerInterface


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
