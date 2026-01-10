"""Base abstract class for OPX hardware handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from qm import FullQuaConfig

from ..simulation import SimulationData
from .opx_context import OPXContext, OPXManagerAndMachine


class BaseOpxHandler(ABC):
    """Abstract base class for OPX hardware handlers.

    Handlers manage access to quantum hardware with two workflows:
    - Execution: open() → execute() → close()
    - Simulation: open() → simulate() → close()

    The program callable is provided at construction time, enabling handler
    reuse and separation of program definition from execution.

    Responsibilities:
        - Device connection lifecycle (open/close)
        - Program building from callable
        - Program execution on hardware
        - Program simulation (without hardware)
        - Context generation and management

    Extensibility:
        Subclass to customize behavior for different hardware configurations,
        simulation modes, or lifecycle patterns (e.g., keep-alive, multi-machine).

    Example - Basic usage:
        >>> handler = DefaultOpxHandler(metadata, config, my_program)
        >>> mm = handler.open()
        >>> ctx = handler.execute(mm)
        >>> data = ctx.result_handles.get('I').fetch_all()
        >>> handler.close()

    Example - Custom keep-alive handler:
        >>> class KeepAliveHandler(DefaultOpxHandler):
        ...     def close(self):
        ...         if self.keep_alive:
        ...             return  # Skip closing
        ...         super().close()
    """

    @abstractmethod
    def __init__(
        self,
        opx_metadata,
        config: FullQuaConfig,
        program_callable: Callable[[], None]
    ):
        """Initialize handler with metadata, config, and program.

        Args:
            opx_metadata: Connection details (host, port, cluster name).
            config: QUA configuration dictionary.
            program_callable: Function containing QUA program logic.
                            Called within 'with program() as prog:' context.
        """
        pass

    @abstractmethod
    def open(self) -> OPXManagerAndMachine:
        """Open connection to quantum hardware.

        Returns:
            OPXManagerAndMachine: Tuple-like object with manager and machine.

        Raises:
            OpenQmException: If hardware connection fails.
        """
        pass

    @abstractmethod
    def execute(self, manager_and_machine: OPXManagerAndMachine) -> OPXContext:
        """Execute the program on hardware.

        Args:
            manager_and_machine: Opened hardware connection from open().

        Returns:
            OPXContext: Execution context with job, result handles, and debug script.
        """
        pass

    @abstractmethod
    def create_qua_scirpt(self) -> str:
        pass

    @abstractmethod
    def simulate(
        self,
        manager_and_machine: OPXManagerAndMachine,
        duration_ns: int,
        flags: list[str] | None = None,
        simulation_interface=None
    ) -> SimulationData:
        """Simulate the program without hardware execution.

        Args:
            manager_and_machine: Opened hardware connection from open().
            duration_ns: Simulation duration in nanoseconds.
            flags: Optional simulation flags (e.g., ['auto-element-thread']).
            simulation_interface: Optional QM simulation interface.

        Returns:
            Simulation data from QM simulator.
        """
        pass

    @abstractmethod
    def close(self, manager_and_machine: OPXManagerAndMachine) -> None:
        """Close connection to quantum hardware.

        Raises:
            QmFailedToCloseQuantumMachineError: If close fails.
        """
        pass

