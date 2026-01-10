# Snapshot experiment: fetch all accumulated data at once

from abc import abstractmethod
from typing import Any, Generic, TypeVar

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure

from ..artefacts_registry import ArtefactRegistry
from ..base import BaseOPX
from ..constants import ExportConstants
from ..handler import BaseOpxHandler, OPXContext
from ..tools import Averager, AveragerInterface
from .interface import LivePlottingInterface, SnapshotInterface
from .solver import SnapshotStrategy, solve_strategy

T = TypeVar("T")


class SnapshotOPX(BaseOPX, Generic[T]):
    """Snapshot OPX template for experiments with continuous data accumulation.

    Designed for programs where data is continuously updated and always accessible.
    The fetch_results() method retrieves all accumulated data from beginning to time t.
    No backpressure needed as data cannot be overwritten.

    Abstract Methods:
        define_program(): Define QUA program (from BaseOPX).
        construct_opx_handler(): Create OPX handler for hardware lifecycle (from BaseOPX).
        fetch_results(): Fetch all accumulated results from hardware.

    Optional Methods:
        pre_run(): Setup before execution.
        post_run(data): Post-process fetched data (default: return unchanged).
        setup_plot(): Setup matplotlib Figure/Artists for live animation.
        update_plot(artists, data): Update plot with new data.

    Strategies:
        Four execution strategies available via execute(strategy=...):
            wait_for_all: Minimal (no live updates).
            wait_for_progress: Adds progress bar.
            live_plotting: Adds real-time animation.
            live_plotting_with_progress: Full-featured (default).
    """

    # Abstract - user must implement
    def __init__(self):
        super().__init__()  # Initialize BaseOPX contract (handler, context, averager)
        self.name = ""
        self.data: Any = None
        self.parameters: Any = None
        self._registry: ArtefactRegistry = ArtefactRegistry()


    @abstractmethod
    def fetch_results(self):
        """Fetch results from hardware."""
        pass

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
        figure_and_artists = self.setup_plot()
        if figure_and_artists is None:
            raise ValueError("Please implement setup plot")
        fig, artists = figure_and_artists
        _ = self.update_plot(artists, data)
        return fig

    # Execution
    def execute(
        self,
        strategy: SnapshotStrategy = "live_plotting_with_progress",
        show_execution_graph: bool = False,
    ) -> T:
        """Execute snapshot experiment with workflow."""

        # Reset and setup
        self._registry.reset()
        self._registry.register(ExportConstants.PARAMETERS, self.parameters)
        self.pre_run()

        self._registry.register(ExportConstants.QUA_SCRIPT, self.opx_handler.create_qua_scirpt())

        # Open hardware and execute
        opx_context = self._open_hardware()

        # Build and execute workflow
        interface = self._create_interface(opx_context)

        # Solve strategy and execute workflow using local solver
        workflow = solve_strategy(strategy, interface)

        if not workflow.empty:
            if show_execution_graph:
                workflow.visualize()
                plt.show()
            workflow.execute()

        # Final fetch and process
        raw_data = self.fetch_results()
        self.data = self.post_run(raw_data)
        self._registry.register(ExportConstants.DATA, self.data)

        # Close
        self._close_hardware()
        return self.data

    def _create_interface(self, opx_context: OPXContext) -> SnapshotInterface:
        """
        Create snapshot interface with all required components.

        Consolidates all interface creation logic:
        - Loads averager interface if averager is used
        - Checks if user implemented optional methods (setup_plot, update_plot)
        - Creates LivePlottingInterface only if plotting methods are implemented
        - Assembles complete SnapshotInterface for workflow strategies

        Returns:
            SnapshotInterface with all components properly initialized
        """

        # Load averager interface if averager is used
        averager_interface = None
        if self._averager is not None:
            averager_interface = self.averager.generate_interface(opx_context.result_handles)
            self._averager_interface = averager_interface

        # Create live plotting interface only if both methods implemented

        live_plotting_interface = LivePlottingInterface(
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            averager_interface=averager_interface,
        )

        # Create main snapshot interface
        return SnapshotInterface(
            fetch_results=self.fetch_results,
            post_run=self.post_run,
            experiment_name=self.name,
            opx_context=opx_context,
            averager_interface=averager_interface,
            live_plotting=live_plotting_interface,
        )
