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
        interface = self._create_interface()

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

    def _is_method_implemented(self, method_name: str) -> bool:
        """
        Check if user implemented an optional method.

        Method is considered implemented if it exists on the class
        and is not the base class placeholder (has been overridden).

        Args:
            method_name: Name of the method to check

        Returns:
            True if method is implemented by user, False otherwise
        """
        method = getattr(self, method_name, None)
        if method is None:
            return False

        # Check if it's the base class implementation (not overridden)
        base_method = getattr(BatchOPX, method_name, None)
        if base_method and hasattr(method, '__func__') and hasattr(base_method, '__func__'):
            return method.__func__ != base_method.__func__

        # If base doesn't have the method, user must have implemented it
        return True

    def _create_interface(self) -> BatchInterface:
        """
        Create batch interface with all required components.

        Consolidates all interface creation logic:
        - Loads averager interface if averager is used
        - Checks if user implemented optional methods (setup_plot, update_plot)
        - Creates LivePlottingInterface only if plotting methods are implemented
        - Assembles complete BatchInterface for workflow strategies

        Returns:
            BatchInterface with all components properly initialized
        """
        # Load averager interface if averager is used
        averager_interface = None
        if self._averager is not None:
            averager_interface = self.averager.generate_interface(
                self.opx_context.result_handles
            )
            self._averager_interface = averager_interface

        # Check if user implemented live plotting methods
        has_setup_plot = self._is_method_implemented('setup_plot')
        has_update_plot = self._is_method_implemented('update_plot')

        # Create live plotting interface only if both methods implemented
        from .interface import LivePlottingInterface
        live_plotting_interface = None
        if has_setup_plot and has_update_plot:
            live_plotting_interface = LivePlottingInterface(
                setup_plot=self.setup_plot,
                update_plot=self.update_plot,
                averager_interface=averager_interface
            )

        # Create main batch interface
        return BatchInterface(
            fetch_results=self.fetch_results,
            post_run=self.post_run,
            experiment_name=self.name,
            opx_context=self.opx_context,
            averager_interface=averager_interface,
            live_plotting=live_plotting_interface
        )
