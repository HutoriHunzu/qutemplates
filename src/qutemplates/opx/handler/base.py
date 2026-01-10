"""Abstract handler for OPX hardware lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from qm import FullQuaConfig

from ..simulation import SimulationData
from .opx_context import OPXContext, OPXManagerAndMachine


class BaseOpxHandler(ABC):
    """Abstract base class for OPX hardware handlers.

    Handlers manage access to quantum hardware with two workflows:
    - Execution: open() -> execute() -> close()
    - Simulation: open() -> simulate() -> close()

    The program callable is provided at construction time, enabling handler
    reuse and separation of program definition from execution.

    Convenience methods open_and_execute() and open_and_simulate() are provided
    for simpler usage patterns.

    Attributes:
        _manager_and_machine: Stored connection for convenience methods.
    """

    _manager_and_machine: OPXManagerAndMachine | None = None

    @abstractmethod
    def __init__(self, opx_metadata, config: FullQuaConfig, program_callable: Callable[[], None]):
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
    def create_qua_script(self) -> str:
        """Generate QUA script string from the program.

        Returns:
            QUA script as a string for debugging or inspection.
        """
        pass

    @abstractmethod
    def simulate(
        self,
        manager_and_machine: OPXManagerAndMachine,
        duration_ns: int,
        flags: list[str] | None = None,
        simulation_interface=None,
    ) -> SimulationData:
        """Simulate the program without hardware execution.

        Args:
            manager_and_machine: Opened hardware connection from open().
            duration_ns: Simulation duration in nanoseconds.
            flags: Optional simulation flags (e.g., ['auto-element-thread']).
            simulation_interface: Optional QM simulation interface.

        Returns:
            SimulationData: Results from QM simulator.
        """
        pass

    @abstractmethod
    def close(self, manager_and_machine: OPXManagerAndMachine | None = None) -> None:
        """Close connection to quantum hardware.

        Args:
            manager_and_machine: Connection to close. If None, uses stored connection.

        Raises:
            QmFailedToCloseQuantumMachineError: If close fails.
        """
        pass

    @property
    @abstractmethod
    def context(self) -> OPXContext:
        """Current execution context. Available after execute() or open_and_execute()."""
        pass

    def open_and_execute(self) -> OPXContext:
        """Open hardware, execute program, and return context.

        Convenience method that manages OPXManagerAndMachine internally.
        The context is stored and accessible via the context property.

        Returns:
            OPXContext: Execution context with job and result handles.
        """
        self._manager_and_machine = self.open()
        return self.execute(self._manager_and_machine)

    def open_and_simulate(
        self, duration_ns: int, flags: list[str] | None = None, simulation_interface=None
    ) -> SimulationData:
        """Open hardware, simulate program, close connection, and return data.

        Convenience method that handles the full simulation lifecycle.

        Args:
            duration_ns: Simulation duration in nanoseconds.
            flags: Optional simulation flags.
            simulation_interface: Optional QM simulation interface.

        Returns:
            SimulationData: Results from QM simulator.
        """
        mm = self.open()
        try:
            return self.simulate(mm, duration_ns, flags, simulation_interface)
        finally:
            self.close(mm)
