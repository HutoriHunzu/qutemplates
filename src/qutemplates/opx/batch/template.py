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
        # URI: should be changed to export_interface (not need to add the batch prefix)
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

    def _create_interface(self) -> BatchInterface:
        """Create interface for workflow."""
        # URI: I want to place all interface related stuff in the same function;
        # checks if averager is valid, if yes make averager averager interface
        # checks if setup plot and update plot are valid (basically the idea here is that the user can either implement them or not, if they are not implemented it just means the strategy of live plotting and others cannot be taken place). i think we should just somehow checks if the user implemented it (hopefully it can be easy but if not than i would go about something else as i dont want it to be difficult), if he doesnt the live_plotting interface (something new, containing setup plot, update plot and averager interface) is none (the solver will know not to call for something depends on it), otherwise pass to the batch interface it.


        return BatchInterface(
            fetch_results=self.fetch_results,
            post_run=self.post_run,
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            experiment_name=self.name,
            opx_context=self.opx_context,
            averager_interface=self._averager_interface
        )
