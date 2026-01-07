"""
LiveAnimationTask - Real-time matplotlib animation task.

Provides a generic task for running matplotlib animations in the main thread
with real-time data updates. Platform-agnostic and reusable across different
workflow systems.
"""

import threading
from typing import Callable, Any, TypeVar
import pathlib

from matplotlib.figure import Figure
from matplotlib.artist import Artist
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from PyQt6.QtCore import QTimer

from quflow import Task, TaskContext
from quflow.status import Status


# Load button icons from resources
dir_path = pathlib.Path(__file__).parent.absolute()
RESOURCES = dir_path / 'resources'
STOP_ICON = plt.imread(str(RESOURCES / 'stop_icon.jpg'))
SAVE_ICON = plt.imread(str(RESOURCES / 'save_icon.png'))

T = TypeVar('T')

SetupFuncType = Callable[[], tuple[Figure, list[Artist]]]
CleanupFuncType = Callable[[tuple[Figure, list[Artist]]], None]
UpdateFuncType = Callable[[list[Artist], T], list[Artist]]


class LiveAnimationTask(Task):
    """
    Runs a Matplotlib animation in the main thread, updating plots in real-time.

    This is a generic, platform-agnostic task that can be used with any workflow
    system. All configuration is provided via constructor (dependency injection).

    The animation continuously reads data and updates matplotlib artists until
    a stop condition is met. Includes built-in stop/continue buttons.

    Args:
        setup_func: Must return (figure, [artist1, artist2, ...]).
                   Called once during setup to create the plot.
        update: Function (artists, data) -> updated_artists.
                Called repeatedly to update plot with new data.
        refresh_time_sec: Interval between animation frames in seconds.
                         Defaults to 0.05 (20 FPS).
        cleanup_func: Optional cleanup routine called after animation stops.
        stop_callable: Function returning bool indicating if animation should stop.
                      Checked on each frame. Defaults to never stop.
        current_avg_callable: Optional function returning current average count.
                             If provided (along with max_avg_callable), displays "n=X/Y".
        max_avg_callable: Optional function returning maximum average count.

    Usage:
        >>> def setup():
        ...     fig, ax = plt.subplots()
        ...     line, = ax.plot([], [])
        ...     return fig, [line]
        ...
        >>> def update(artists, data):
        ...     line = artists[0]
        ...     line.set_data(data['x'], data['y'])
        ...     return [line]
        ...
        >>> task = LiveAnimationTask(
        ...     setup_func=setup,
        ...     update=update,
        ...     stop_callable=lambda: experiment_done
        ... )

    Note:
        This task should be run in the main thread (run_in_main_thread=True)
        to avoid concurrency issues with matplotlib.

        Data is read via context.read_callable() which should be set up
        by the workflow system to provide the data channel.
    """

    def __init__(
        self,
        *,
        setup_func: SetupFuncType,
        update: UpdateFuncType,
        refresh_time_sec: float = 0.05,
        current_avg_callable: Callable[[], int] | None = None,
        max_avg: int | None = None
    ):

        # User-provided callbacks (dependency injection)
        self.update = update
        self.setup_func = setup_func
        self.current_avg_callable = current_avg_callable
        self.max_avg = max_avg

        # Animation state
        self.figure: Figure | None = None
        self.artists: list[Artist] | None = None
        self.animation = None
        self.refresh_time_ms: int = int(refresh_time_sec * 1000)
        self.exception = None

        # Task context (set during run)
        self._context: TaskContext | None = None

        # UI elements
        self._stop_button = None
        self._continue_button = None
        self._text_artist_for_avg = None

    @property
    def context(self):
        """Get the task execution context."""
        return self._context

    def update_average(self) -> tuple:
        """
        Update the average counter text display.

        Returns:
            Tuple containing the text artist if averager is enabled, empty tuple otherwise.
        """
        if self._text_artist_for_avg is None:
            return ()

        current_avg = self.current_avg_callable()
        max_avg = self.max_avg

        if current_avg and max_avg:
            text = self._get_averager_text_formatter(current_avg, max_avg)
            self._text_artist_for_avg.set_text(text)

        return (self._text_artist_for_avg, )

    def stop_from_animation(self):
        """Stop animation and close figure (called from animation loop)."""
        QTimer.singleShot(0, lambda: plt.close(self.figure))

    @staticmethod
    def _get_averager_text_formatter(curr_avg=None, max_avg=None):
        """Format average counter text."""
        if curr_avg is None or max_avg is None:
            return "n=?/?"
        return f"n={curr_avg}/{max_avg:g}"

    def _setup_averager_artist(self) -> Artist:
        """Create text artist for displaying average counter."""
        text = self._get_averager_text_formatter()
        return self.figure.text(
            x=1.0,
            y=1.0,
            s=text,
            fontsize='large',
            horizontalalignment='right',
            verticalalignment='top'
        )

    def setup(self):
        """
        Set up the plot by calling user's setup_func.

        Creates the figure, artists, optional averager display, and control buttons.
        """
        # Call user's setup function
        self.figure, self.artists = self.setup_func()

        # Add averager text if callbacks provided
        if self.current_avg_callable is not None and self.max_avg is not None:
            self._text_artist_for_avg = self._setup_averager_artist()

        # Add control buttons
        self.add_stop_button()
        self.add_continue_button()

    def execute(self):
        """
        Execute the animation loop.

        Creates FuncAnimation and runs plt.show() which blocks until figure is closed.
        """
        self.animation = FuncAnimation(
            fig=self.figure,
            func=self.step,
            interval=self.refresh_time_ms,
            blit=False,
            repeat=True,
            frames=200
        )

        # This blocks until the figure is closed
        plt.show()

        # Signal interrupt when animation ends
        self.context.interrupt.set()

    def run(self, ctx: TaskContext) -> Status:
        """
        Main task execution method called by the workflow system.

        Args:
            ctx: Task execution context providing interrupt events and data channels

        Returns:
            Status.FINISHED when animation completes
        """
        self._context = ctx

        self.setup()
        self.execute()

        return Status.FINISHED

    def stop_from_button(self):
        """Stop animation and close figure (called from button click)."""
        # Stop the animation's event source
        if self.animation is not None:
            self.animation.event_source.stop()

        # Close the figure so that plt.show() returns
        if self.figure is not None:
            plt.close(self.figure)


    def stop_when_button_pressed(self, event):
        """Handler for stop button click."""
        self.stop_from_button()

    def continue_when_button_pressed(self, event):
        """Handler for continue/save button click."""
        self.stop_from_button()

    def add_stop_button(self):
        """Add stop button to the figure."""
        ax_stop = self.figure.add_axes([0.1, 0.9, 0.08, 0.08])
        ax_stop.set_axis_off()
        self._stop_button = Button(ax_stop, '', image=STOP_ICON)
        self._stop_button.on_clicked(self.stop_when_button_pressed)

    def add_continue_button(self):
        """Add continue/save button to the figure."""
        ax_continue = self.figure.add_axes([0.9, 0.9, 0.08, 0.08])
        ax_continue.set_axis_off()
        self._continue_button = Button(ax_continue, '', image=SAVE_ICON)
        self._continue_button.on_clicked(self.continue_when_button_pressed)


    def step(self, frame):
        """
        Animation step function called repeatedly by FuncAnimation.

        Reads new data from context, updates artists, checks stop conditions.

        Args:
            frame: Frame number (provided by FuncAnimation)

        Returns:
            Tuple of artists that were updated (for blitting)
        """

        artists = self.artists

        try:
            # Check stop conditions
            if self.context.interrupt.is_set():
                self.stop_from_animation()

            # Read new data from channel
            data = self.context.read_callable()

            if data is not None:
                # Update artists with new data
                artists = self.update(self.artists, data)
                # Update average counter if enabled
                text_artist_as_tuple = self.update_average()
                artists = (*artists, *text_artist_as_tuple)

        except Exception as e:
            # Store exception and stop animation
            self.exception = e
            self.stop_from_animation()
            self.context.interrupt.set()

        # Return all artists for blitting
        return artists
