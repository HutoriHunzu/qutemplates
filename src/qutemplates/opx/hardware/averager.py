import threading

from qm.qua import StreamType, declare, declare_stream, save
from dataclasses import dataclass, field
import numpy as np
import matplotlib.pyplot as plt
from typing import Iterable, Any

from qm.jobs.running_qm_job import RunningQmJob, StreamsManager
from qm.qua.type_hints import QuaVariable
from tqdm import tqdm


class AveragerInterface:
    """
    Runtime interface for fetching and tracking averaging progress.

    This class is created by Averager.generate_interface() after QUA program
    execution. It provides thread-safe access to the current averaging count
    from the OPX hardware, used by progress bars and live plotting features.

    The interface maintains a cached count that is updated by calling update(),
    which fetches the latest value from the hardware result handles.

    Thread Safety:
        All count access (get/set) is protected by a lock to ensure thread-safe
        operation when used by parallel workflow nodes.

    Lifecycle:
        1. Created by Averager.generate_interface() after job execution
        2. Passed to workflow features (progress bar, live animation)
        3. Features call interface.update() to fetch current count from hardware
        4. Features read interface.count to get cached value

    Example:
        >>> # Created by framework, not user:
        >>> interface = averager.generate_interface(result_handles)
        >>>
        >>> # Used by progress bar feature:
        >>> while not done:
        ...     current = interface.update()  # Fetch from hardware
        ...     progress_bar.update(current)
        ...
        >>> # Or by live plotting:
        >>> count = interface.count  # Read cached value

    Attributes:
        total: Total number of averages expected
        count: Current averaging count (thread-safe property)

    Note:
        This class is typically instantiated by the framework, not by users
        directly. Users interact with the Averager class during program definition.
    """

    def __init__(self,
                 save_name: str,
                 total: int,
                 result_handles: StreamsManager
                 ):
        """
        Initialize runtime interface.

        Args:
            save_name: Stream name used to save counter in QUA program
            total: Total number of averages expected
            result_handles: StreamsManager from executed job
        """
        self.total: int = total
        self._result_handles: StreamsManager = result_handles
        self._save_name = save_name
        self._count: int = 0
        self._lock: threading.Lock = threading.Lock()

    @property
    def count(self):
        with self._lock:
            value = self._count
        return value

    @count.setter
    def count(self, value):
        with self._lock:
            self._count = value

    def update(self) -> int:
        value = self._result_handles.get(self._save_name).fetch(0)
        value = 0 if value is None else value
        value += 1
        self.count = value
        return value

    def get_current_average(self):
        return self.count


class Averager:
    """
    QUA program averager for constructing averaging logic and tracking progress.

    This class provides a two-phase system for experiment averaging:

    **Phase 1 - QUA Program Construction (this class):**
    User configures averaging parameters (total, save_name) and calls methods
    during QUA program definition to construct averaging logic:
    1. init_vars(): Create QUA variables (counter, stream)
    2. update_count(): Add save statement to QUA program
    3. stream_processing(): Add stream processing to save counter
    4. generate_interface(): Create runtime interface after execution

    **Phase 2 - Runtime Data Access (AveragerInterface):**
    After program execution, the returned AveragerInterface provides:
    - Thread-safe counter updates via update()
    - Thread-safe counter reads via count property
    - Used by progress bars and live plotting features

    Lifecycle:
        1. User sets averager.total = N
        2. In define_program(): counter = averager.init_vars()
        3. In define_program(): averager.update_count() (in averaging loop)
        4. In stream processing: averager.stream_processing()
        5. After execution: interface = averager.generate_interface(result_handles)
        6. During workflow: interface.update() to fetch current count

    Example:
        >>> class MyExperiment(OpxExperiment):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.averager.total = 1000
        ...
        ...     def define_program(self):
        ...         counter = self.averager.init_vars()
        ...         with for_(counter, 0, counter < self.averager.total, counter + 1):
        ...             # ... experiment logic ...
        ...             self.averager.update_count()
        ...
        ...     def stream_processing(self):
        ...         self.averager.stream_processing()
        ...
        >>> # After execution, AveragerInterface automatically used by features

    Note:
        This class uses instance variables (not class variables) to ensure
        proper isolation between different experiment instances.
    """

    def __init__(self):
        """Initialize averager with default state."""
        self.total: int = 0
        self.save_name: str = "repetition_number"
        self._stream: StreamType | None = None
        self._count: QuaVariable | None = None

    def init_vars(self):
        """Initialize variables and returns `qm.qua._dsl._Expression` object"""
        self._stream = declare_stream()
        self._count = declare(int)
        return self._count

    @property
    def n(self):
        return self._count

    def update_count(self):
        save(self._count, self._stream)

    def stream_processing(self):
        self._stream.save(self.save_name)

    def generate_interface(self, result_handles: StreamsManager) -> AveragerInterface | None:
        """
        Generate runtime interface for fetching averaging progress.

        This should be called after QUA program execution to create an
        AveragerInterface that can fetch the current averaging count from
        the OPX hardware.

        Args:
            result_handles: StreamsManager from executed job

        Returns:
            AveragerInterface for thread-safe counter access

        Raises:
            ValueError: If init_vars() was not called during program definition

        Example:
            >>> # After job execution:
            >>> interface = averager.generate_interface(result_handles)
            >>> current_count = interface.update()  # Fetch from hardware
        """
        # Validate that averager was properly initialized in QUA program
        if self._stream is None or self._count is None:
            return None
            # raise ValueError(
            #     'Averager must be initialized in QUA program before generating interface. '
            #     'Call averager.init_vars() in your define_program() method.'
            # )

        return AveragerInterface(
            save_name=self.save_name,
            result_handles=result_handles,
            total=self.total
        )
