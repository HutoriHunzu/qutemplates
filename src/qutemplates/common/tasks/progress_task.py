"""
ProgressTask - Generic progress bar task using tqdm.

Provides a platform-agnostic task for displaying progress during long-running
operations. Polls user-provided callbacks to update the progress bar.
"""

from typing import Callable

from tqdm import tqdm
from quflow.tasks.base import Task, TaskContext
from quflow.status import Status


class ProgressTask(Task):
    """
    Generic progress bar task using tqdm.

    Continuously polls callbacks to get current progress and updates a tqdm
    progress bar until a stop condition is met. All errors from callbacks
    propagate to the caller.

    This is a platform-agnostic task suitable for any workflow system.
    All configuration is provided via constructor (dependency injection).

    Args:
        get_current: Callable returning current progress value (int or float).
                    Called repeatedly during execution. Errors propagate.
        get_total: Callable returning total/maximum progress value.
                  Can return None if total is unknown. Errors propagate.
        title: Progress bar description/title. Defaults to "Progress".
        stop_callable: Callable returning bool indicating if task should stop.
                      Checked on each iteration. Defaults to never stop.
        refresh_interval: Time in seconds between progress updates.
                         Defaults to 0.1 (10 updates per second).

    Usage:
        >>> def get_current_count():
        ...     return experiment.samples_processed
        ...
        >>> def get_total_count():
        ...     return experiment.total_samples
        ...
        >>> task = ProgressTask(
        ...     get_current=get_current_count,
        ...     get_total=get_total_count,
        ...     title="Processing Samples",
        ...     stop_callable=lambda: experiment.is_done()
        ... )

    Note:
        This task does NOT catch exceptions from callbacks. If get_current()
        or get_total() raise an exception, it will propagate to the caller.
        This is intentional - users should see and handle errors.

        The progress bar is automatically closed during cleanup, even if
        the task is interrupted.
    """

    def __init__(
        self,
        get_current: Callable[[], int | float],
        total: int,
        title: str = "Progress",
    ):
        # User-provided callbacks (dependency injection)
        self.get_current = get_current
        self.total: int = total
        self.title = title

        # Progress bar (created during execution)
        self._pbar: tqdm | None = None

    def setup(self):
        # Create progress bar
        self._pbar = tqdm(total=self.total, desc=self.title)

    def cleanup(self):
        if self._pbar is not None:
            self._pbar.close()

    def update(self):
        # Get current progress
        # Let exceptions propagate - don't catch them
        current = self.get_current()

        extra = current - self._pbar.n
        if extra > 0:  # No new data - skip the post_run() and the plot up
            self._pbar.update(extra)


    def run(self, ctx: TaskContext) -> Status:

        self.setup()

        while not ctx.interrupt.is_set():
            self.update()

        self.cleanup()

        return Status.FINISHED

