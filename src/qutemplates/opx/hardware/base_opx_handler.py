"""Base abstract class for OPX hardware handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from .opx_context import OPXContext


class BaseOpxHandler(ABC):
    """
    Abstract base class for OPX hardware handlers.

    Defines the contract for all OPX handlers:
    - open(): Open quantum machine with configuration
    - close(): Close quantum machine
    - open_and_execute(): Full lifecycle execution
    - context: Access to execution context

    Handlers manage the lifecycle of quantum hardware including:
    - Quantum Machines Manager (QMM) connections
    - Quantum Machine (QM) instances
    - QUA program execution
    - Context generation

    Subclasses must implement these methods to define custom
    hardware management behavior (e.g., simulation, keep-alive,
    multi-machine orchestration).

    Example - Custom simulation handler:
        >>> class SimulationHandler(BaseOpxHandler):
        ...     def __init__(self, opx_metadata, config, duration_ns):
        ...         self.config = config
        ...         self.duration_ns = duration_ns
        ...         self._context = None
        ...
        ...     def open_and_execute(self, program_callable, debug=False):
        ...         # Simulate instead of executing on hardware
        ...         with program() as prog:
        ...             program_callable()
        ...         sim_data = simulate_program(...)
        ...         self._context = OPXContext(...)
        ...         return self._context
        ...
        ...     # ... implement other abstract methods ...

    Example - Keep-alive handler:
        >>> class KeepAliveHandler(DefaultOpxHandler):
        ...     def __init__(self, opx_metadata, config, keep_alive=True):
        ...         super().__init__(opx_metadata, config)
        ...         self.keep_alive = keep_alive
        ...
        ...     def close(self):
        ...         if self.keep_alive:
        ...             return  # Skip closing
        ...         super().close()
    """

    @abstractmethod
    def open(self, config: dict):
        """
        Open quantum machine with given configuration.

        Args:
            config: QUA configuration dictionary

        Returns:
            Tuple of (QuantumMachinesManager, QuantumMachine or QmApi)

        Raises:
            OpenQmException: If QM fails to open
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the current quantum machine.

        Raises:
            QmFailedToCloseQuantumMachineError: If QM fails to close
        """
        pass

    @abstractmethod
    def open_and_execute(self, program_callable: Callable[[], None], debug: bool = False) -> OPXContext:
        """
        Execute complete hardware lifecycle: open, define program, execute.

        This is the main entry point used by experiments. Configuration
        should already be part of the handler's state (set during construction).

        Args:
            program_callable: Function containing QUA program logic.
                            Called within `with program() as prog:` context.
                            Signature: () -> None
            debug: If True, generates debug script

        Returns:
            OPXContext with job, result handles, QM, and optional debug script

        Example:
            >>> def my_program():
            ...     measure('readout', 'qubit', None, ...)
            >>>
            >>> handler = DefaultOpxHandler(opx_metadata, config)
            >>> ctx = handler.open_and_execute(my_program, debug=True)
            >>> data = ctx.result_handles.get('I').fetch_all()
        """
        pass

    @property
    @abstractmethod
    def context(self) -> OPXContext:
        """
        Current OPX execution context.

        Returns:
            OPXContext containing job, result handles, and QM

        Raises:
            ValueError: If context not yet initialized (call open_and_execute first)
        """
        pass
