"""Feature context - clean interface for features without full experiment coupling."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .control_panel import ControlPanel
    from .protocol.experiment import ExperimentProtocol
    from .protocol.data_source import DataSource
    from .protocol.progress_source import ProgressSource


class FeatureContext:
    """
    Provides features with what they need without coupling to full experiment.

    Instead of features depending on the entire experiment class with all its
    properties and methods, they depend on this focused context that exposes
    only what features typically need.

    This keeps the feature interface stable even if the experiment implementation
    changes, and makes it clear what capabilities features depend on.
    """

    def __init__(
        self,
        control_panel: 'ControlPanel',
        experiment: 'ExperimentProtocol',
    ):
        """
        Initialize feature context.

        Args:
            control_panel: Central control signals and state
            experiment: The experiment instance (for calling user-defined methods)
        """
        self.control_panel = control_panel
        self.experiment = experiment

    def is_running(self) -> bool:
        """Check if experiment is still running."""
        return self.control_panel.is_running()

    def should_stop(self) -> bool:
        """Check if stop has been requested."""
        return self.control_panel.should_stop()

    # ==================== Capability Accessors ====================

    def get_data_source(self) -> 'DataSource | None':
        """
        Get data source capability if experiment provides it.

        Features that need to access data (live plotting, analysis)
        should use this instead of directly accessing experiment internals.

        Returns:
            DataSource implementation if available, None otherwise
        """
        from .protocol.data_source import DataSource
        if isinstance(self.experiment, DataSource):
            return self.experiment
        return None

    def get_progress_source(self) -> 'ProgressSource | None':
        """
        Get progress source capability if experiment provides it.

        Features that need progress information (progress bars, status displays)
        should use this instead of directly accessing experiment internals.

        Returns:
            ProgressSource implementation if available, None otherwise
        """
        from .protocol.progress_source import ProgressSource
        if isinstance(self.experiment, ProgressSource):
            return self.experiment
        return None

    def has_capability(self, capability_type: type) -> bool:
        """
        Check if experiment provides a specific capability.

        Args:
            capability_type: The capability class to check for

        Returns:
            True if experiment implements this capability
        """
        return isinstance(self.experiment, capability_type)
