# Streaming experiment: incremental chunk semantics

from __future__ import annotations

from abc import abstractmethod
from queue import Queue
from typing import Any, Generic, TypeVar

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure

from ..artefacts_registry import ArtefactRegistry
from ..base import BaseOPX
from ..constants import ExportConstants
from ..handler import BaseOpxHandler, OPXContext
from ..simulation import SimulationData
from ..tools import Averager, AveragerInterface
from .interface import StreamingInterface
from .solver import StreamingStrategy, solve_strategy

T = TypeVar("T")


class StreamingOPX(BaseOPX, Generic[T]):
    """Streaming template: user controls fetch loop via program_coordinator.

    For experiments with incremental chunk-based data fetching.
    Implement define_program(), construct_opx_handler(), and program_coordinator().
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = ""
        self.data: Any = None
        self.parameters: Any = None
        self._registry = ArtefactRegistry()
        self._averager: Averager | None = None
        self._averager_interface: AveragerInterface | None = None

    @property
    def averager(self) -> Averager:
        """Lazily constructed averager for progress tracking."""
        if self._averager is None:
            self._averager = Averager()
        return self._averager

    @property
    def averager_interface(self) -> AveragerInterface | None:
        """Averager interface, available after execution starts."""
        return self._averager_interface

    # Abstract - user must implement

    @abstractmethod
    def program_coordinator(self, job, result_handles, output_queue: Queue):
        """User controls fetch loop. Called ONCE by framework. Writes chunks to queue."""

    # Optional - user can override

    def get_aggregated_data(self) -> Any:
        """Return aggregated data from coordinator. Optional - for testing."""
        return None

    def pre_run(self):
        """Setup before execution."""
        pass

    def post_run(self, data) -> T:
        """Process chunks/aggregated data. Default: return unchanged."""
        return data

    def setup_plot(self) -> tuple[Figure, list[Artist]]:
        """Setup plot for live animation."""
        pass

    def update_plot(self, artists: list[Artist], data: T) -> list[Artist]:
        """Update plot with new data."""
        return artists

    # Execution

    def execute(
        self,
        strategy: StreamingStrategy = "live_plotting_with_progress",
        show_execution_graph: bool = False,
    ) -> T:
        """Execute streaming experiment with workflow."""
        # Setup
        self._registry.reset()
        self._registry.register(ExportConstants.PARAMETERS, self.parameters)
        self.pre_run()
        self._registry.register(ExportConstants.QUA_SCRIPT, self.opx_handler.create_qua_script())

        # Open hardware and execute
        opx_context = self.opx_handler.open_and_execute()

        # Load averager interface if averager is used
        averager_interface = None
        if self._averager is not None:
            averager_interface = self.averager.generate_interface(opx_context.result_handles)
            self._averager_interface = averager_interface

        # Build and execute workflow
        interface = self._create_streaming_interface(opx_context, averager_interface)
        workflow = solve_strategy(strategy, interface)

        if not workflow.empty:
            if show_execution_graph:
                workflow.visualize()
                plt.show()
            workflow.execute()

        # Get aggregated data and post-process
        raw_data = self.get_aggregated_data()
        if raw_data is not None:
            self.data = self.post_run(raw_data)

        self._registry.register(ExportConstants.DATA, self.data)
        self.opx_handler.close()

        return self.data

    def simulate(
        self,
        duration_ns: int,
        debug_path: str | None = None,
        auto_element_thread: bool = False,
        not_strict_timing: bool = False,
        simulation_interface=None,
    ) -> SimulationData:
        """Simulate program without hardware execution."""
        self.pre_run()

        flags: list[str] = []
        if auto_element_thread:
            flags.append("auto-element-thread")
        if not_strict_timing:
            flags.append("not-strict-timing")

        data = self.opx_handler.open_and_simulate(duration_ns, flags, simulation_interface)

        if debug_path:
            with open(debug_path, "w") as f:
                f.write(self.opx_handler.create_qua_script())

        return data

    # Internal

    def _create_streaming_interface(
        self,
        opx_context: OPXContext,
        averager_interface: AveragerInterface | None,
    ) -> StreamingInterface:
        """Create interface for workflow."""
        return StreamingInterface(
            program_coordinator=self.program_coordinator,
            post_run=self.post_run,
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            experiment_name=self.name,
            opx_context=opx_context,
            averager_interface=averager_interface,
        )
