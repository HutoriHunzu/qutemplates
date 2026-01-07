# Batch experiment: fetch-all semantics

from abc import abstractmethod
from typing import TypeVar

from matplotlib.artist import Artist
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from ..base import BaseOPX
from .interface import BatchInterface
from .solver import BatchStrategy, solve_strategy
from ..constants import ExportConstants


T = TypeVar('T')


class BatchOPX(BaseOPX[T]):
    """Batch: run to completion, fetch all, process."""

    # Abstract - user must implement

    @abstractmethod
    def fetch_results(self):
        """Fetch results from hardware."""
        pass

    # Optional - user can override

    def pre_run(self):
        """Setup before execution."""
        pass

    def post_run(self, data) -> T:
        """Process fetched data. Default: return unchanged."""
        return data

    def setup_plot(self) -> tuple[Figure, list[Artist]] | None:
        """Setup plot for live animation."""
        pass

    def update_plot(self, artists: list[Artist], data: T) -> list[Artist]:
        """Update plot with new data."""
        return artists

    # Execution

    def execute(
        self,
        strategy: BatchStrategy = 'live_plotting_with_progress',
        debug_script_path: str | None = None,
        show_execution_graph: bool = False,
    ) -> T:
        """Execute batch experiment with workflow."""

        # Reset and setup
        self.reset()
        self.register_data(ExportConstants.PARAMETERS, self.parameters)
        self.pre_run()

        # Open hardware
        self._open_hardware()
        self.register_data(ExportConstants.DEBUG, self.opx_context.debug_script)

        # Build and execute workflow
        self._load_averager_interface()
        interface = self._create_batch_interface()

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
        self.register_data(ExportConstants.DATA, self.data)

        # Close
        self._close_hardware()
        return self.data

    # Internal

    def _create_batch_interface(self) -> BatchInterface:
        """Create interface for workflow."""
        return BatchInterface(
            fetch_results=self.fetch_results,
            post_run=self.post_run,
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            experiment_name=self.name,
            opx_context=self.opx_context,
            averager_interface=self._averager_interface
        )
