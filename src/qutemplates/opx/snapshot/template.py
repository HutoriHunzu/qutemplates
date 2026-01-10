"""Snapshot template: fetch all accumulated data at once."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Generic, TypeVar

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure

from qutemplates.export import ArtifactKind, ArtifactRegistry

from ..averager import Averager, AveragerInterface
from ..base import BaseOPX
from ..simulation import SimulationData
from ..utils import ns_to_clock_cycles
from .constants import ExportConstants
from .interface import LivePlottingInterface, SnapshotInterface
from .solver import SnapshotStrategy, solve_strategy

T = TypeVar("T")


class SnapshotOPX(BaseOPX, Generic[T]):
    """Snapshot template: fetch all accumulated data at once.

    For experiments where data accumulates continuously and is fetched at the end.
    Implement define_program(), construct_opx_handler(), and fetch_results().

    Execution strategies: wait_for_all, wait_for_progress, live_plotting,
    live_plotting_with_progress (default).
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = ""
        self.data: Any = None
        self.parameters: Any = None
        self._registry = ArtifactRegistry()
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

    @property
    def artifacts(self) -> ArtifactRegistry:
        """Access registered artifacts."""
        return self._registry

    @abstractmethod
    def fetch_results(self):
        """Fetch results from hardware."""

    def pre_run(self):
        """Setup before execution."""
        pass

    def post_run(self, data) -> T:
        """Process fetched data. Default: return unchanged."""
        return data

    def setup_plot(self) -> tuple[Figure, list[Artist]]:
        """Setup plot for live animation."""
        raise NotImplementedError

    def update_plot(self, artists: list[Artist], data: T) -> list[Artist]:
        """Update plot with new data."""
        raise NotImplementedError

    def plot(self, data: T) -> Figure:
        fig, artists = self.setup_plot()
        self.update_plot(artists, data)
        return fig

    def execute(
        self,
        strategy: SnapshotStrategy = "live_plotting_with_progress",
        show_execution_graph: bool = False,
    ) -> T:
        """Execute snapshot experiment with workflow."""
        # Setup
        self.artifacts.reset()
        self.artifacts.register(ExportConstants.PARAMETERS, self.parameters)
        self.pre_run()
        self.artifacts.register(
            ExportConstants.QUA_SCRIPT, self.create_qua_script(), kind=ArtifactKind.PY
        )

        # Explicit lifecycle: open -> execute -> workflow -> close
        self.opx_handler.open()
        prog = self._build_program()
        self.opx_context = self.opx_handler.execute(prog)

        # Build averager interface if averager was used
        if self._averager is not None:
            self._averager_interface = self.averager.generate_interface(self.opx_context.result_handles)

        # Build and execute workflow
        interface = self._create_interface()
        workflow = solve_strategy(strategy, interface)

        if not workflow.empty:
            if show_execution_graph:
                workflow.visualize()
                plt.show()
            workflow.execute()

        # Final fetch, process, and close
        raw_data = self.fetch_results()
        self.data = self.post_run(raw_data)
        self.artifacts.register(ExportConstants.DATA, self.data)
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
        """Simulate program without hardware execution.

        Args:
            duration_ns: Simulation duration in nanoseconds.
            debug_path: Optional path to save QUA debug script.
            auto_element_thread: Enable auto-element-thread simulation flag.
            not_strict_timing: Enable not-strict-timing simulation flag.
            simulation_interface: Optional QM simulation interface.

        Returns:
            SimulationData from QM simulator.
        """
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

    def _create_interface(self) -> SnapshotInterface:
        """Create snapshot interface with all required components."""
        live_plotting_interface = LivePlottingInterface(
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            averager_interface=self._averager_interface,
        )

        return SnapshotInterface(
            fetch_results=self.fetch_results,
            post_run=self.post_run,
            experiment_name=self.name,
            opx_context=self.opx_context,
            averager_interface=self._averager_interface,
            live_plotting=live_plotting_interface,
        )
