"""Streaming template: incremental chunk-based data fetching."""

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
from ..handler import OPXContext
from ..simulation import SimulationData
from ..averager import Averager, AveragerInterface
from ..utils import ns_to_clock_cycles
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

    @abstractmethod
    def program_coordinator(self, job, result_handles, output_queue: Queue):
        """User controls fetch loop. Called ONCE by framework. Writes chunks to queue."""

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
        raise NotImplementedError

    def update_plot(self, artists: list[Artist], data: T) -> list[Artist]:
        """Update plot with new data."""
        return artists

    def execute(
        self,
        strategy: StreamingStrategy = "live_plotting_with_progress",
        show_execution_graph: bool = False,
    ) -> T:
        """Execute streaming experiment with workflow."""
        self._registry.reset()
        self._registry.register(ExportConstants.PARAMETERS, self.parameters)
        self.pre_run()
        self._registry.register(ExportConstants.QUA_SCRIPT, self.create_qua_script())

        # Explicit lifecycle: open -> execute -> workflow -> close
        self.opx_handler.open()
        prog = self._build_program()
        self._context = self.opx_handler.execute(prog)

        if self._averager is not None:
            self._averager_interface = self.averager.generate_interface(self._context.result_handles)

        interface = self._create_streaming_interface(self._context)
        workflow = solve_strategy(strategy, interface)

        if not workflow.empty:
            if show_execution_graph:
                workflow.visualize()
                plt.show()
            workflow.execute()

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

        # Explicit lifecycle: open -> simulate -> close
        self.opx_handler.open()
        try:
            prog = self._build_program()
            duration_cycles = ns_to_clock_cycles(duration_ns)
            data = self.opx_handler.simulate(prog, duration_cycles, flags, simulation_interface)
        finally:
            self.opx_handler.close()

        if debug_path:
            with open(debug_path, "w") as f:
                f.write(self.create_qua_script())

        return data

    def _create_streaming_interface(self, opx_context: OPXContext) -> StreamingInterface:
        """Create interface for workflow."""
        return StreamingInterface(
            program_coordinator=self.program_coordinator,
            post_run=self.post_run,
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            experiment_name=self.name,
            opx_context=opx_context,
            averager_interface=self._averager_interface,
        )
