"""Control panel - central place for execution control signals and state."""

from dataclasses import dataclass, field
from threading import Event


@dataclass
class ControlPanel:
    """
    Centralized control signals for experiment execution.

    Groups related control events and state queries that are commonly
    passed between the experiment, execution strategy, and features.

    This prevents having to pass multiple separate Event/callable parameters
    throughout the codebase.
    """

    job_is_done: Event = field(default_factory=Event)
    stop_requested: Event = field(default_factory=Event)

    def is_running(self) -> bool:
        """Check if the experiment job is still running."""
        return not self.job_is_done.is_set()

    def request_stop(self) -> None:
        """Request that the experiment stop (user interrupt)."""
        self.stop_requested.set()

    def mark_done(self) -> None:
        """Mark the experiment job as completed."""
        self.job_is_done.set()

    def wait_until_done(self, timeout: float | None = None) -> bool:
        """
        Block until the job is done or timeout expires.

        Args:
            timeout: Maximum time to wait in seconds, None for no timeout

        Returns:
            True if job completed, False if timeout occurred
        """
        return self.job_is_done.wait(timeout=timeout)

    def should_stop(self) -> bool:
        """Check if a stop has been requested."""
        return self.stop_requested.is_set()
