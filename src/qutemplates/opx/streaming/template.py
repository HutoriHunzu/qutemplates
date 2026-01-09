# Streaming experiment: incremental chunk semantics

from abc import abstractmethod
from typing import TypeVar, Any
from queue import Queue

from matplotlib.artist import Artist
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from ..base import BaseOPX
from .interface import StreamingInterface
from .solver import StreamingStrategy, solve_strategy
from ..constants import ExportConstants
from ..hardware import BaseOpxHandler, DefaultOpxHandler


T = TypeVar("T")


class StreamingOPX(BaseOPX[T]):
    """Streaming: user controls fetch loop via program_coordinator."""

    # Abstract - user must implement

    @abstractmethod
    def program_coordinator(self, job, result_handles, output_queue: Queue):
        """User controls fetch loop. Called ONCE by framework. Writes chunks to queue."""
        pass

    def construct_opx_handler(self) -> BaseOpxHandler:
        """
        Create default OPX handler for streaming experiments.

        Override to provide custom handler:
            class MyStreamingExperiment(StreamingOPX):
                def construct_opx_handler(self):
                    return CustomHandler(self.opx_metadata(), self.init_config())

        Returns:
            DefaultOpxHandler configured for this experiment
        """
        return DefaultOpxHandler(self.opx_metadata(), self.init_config())

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
        debug_script_path: str | None = None,
        show_execution_graph: bool = False,
    ) -> T:
        """Execute streaming experiment with workflow."""

        # Reset and setup
        self.reset()
        self.register_data(ExportConstants.PARAMETERS, self.parameters)
        self.pre_run()

        # Open hardware
        self._open_hardware()
        self.register_data(ExportConstants.DEBUG, self.opx_context.debug_script)

        # Build and execute workflow
        self._load_averager_interface()
        interface = self._create_streaming_interface()

        # Solve strategy and execute workflow using local solver
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
        # else: data already set by workflow via post_run

        self.register_data(ExportConstants.DATA, self.data)

        # Close
        self._close_hardware()
        return self.data

    # Internal

    def _create_streaming_interface(self) -> StreamingInterface:
        """Create interface for workflow."""
        return StreamingInterface(
            program_coordinator=self.program_coordinator,
            post_run=self.post_run,
            setup_plot=self.setup_plot,
            update_plot=self.update_plot,
            experiment_name=self.name,
            opx_context=self.opx_context,
            averager_interface=self._averager_interface,
        )
