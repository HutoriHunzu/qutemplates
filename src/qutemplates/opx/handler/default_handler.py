"""Default OPX handler with shared QMM per IP address."""

from __future__ import annotations

from collections.abc import Callable

from qm import FullQuaConfig, QuantumMachinesManager, generate_qua_script
from qm.qua import program

from qutemplates.opx.simulation.structure import SimulationData

from ..simulation import simulate_program
from ..utilities import ns_to_clock_cycles
from .base import BaseOpxHandler
from .opx_context import OPXContext, OPXManagerAndMachine


class DefaultOpxHandler(BaseOpxHandler):
    """Default OPX handler with shared QMM per IP address.

    Standard implementation for most experiments. Features:
    - QMM caching per IP (avoids reconnection overhead)
    - Program building from callable
    - Full execution and simulation support

    Override create_qmm() for custom manager creation (e.g., with Octave).
    """

    # Class-level: Shared QMMs per IP address
    _ip_to_manager: dict[str, QuantumMachinesManager] = {}

    def __init__(
        self,
        opx_metadata,
        config: FullQuaConfig,
        program_callable: Callable[[], None]
    ):
        """Initialize handler with metadata, config, and program.

        Args:
            opx_metadata: OpxMetadata dataclass with connection details.
            config: QUA configuration dictionary.
            program_callable: Function containing QUA program logic.
        """
        self.opx_metadata = opx_metadata
        self.config = config
        self.program_callable = program_callable
        self._context: OPXContext | None = None
        self._manager_and_machine: OPXManagerAndMachine | None = None

    def get_or_create_qmm(self) -> QuantumMachinesManager:
        """Get or create QuantumMachinesManager for this IP address.

        QMM is shared across all handlers connecting to the same IP.
        Override to customize manager lookup/creation logic.

        Returns:
            QuantumMachinesManager instance for this IP.
        """
        ip = self.opx_metadata.host_ip
        if ip not in self._ip_to_manager:
            self._ip_to_manager[ip] = self.create_qmm()
        return self._ip_to_manager[ip]

    def create_qmm(self) -> QuantumMachinesManager:
        """Create new QuantumMachinesManager.

        Override to customize manager creation (e.g., add octave config).

        Returns:
            New QuantumMachinesManager instance.

        Example - Add octave:
            >>> def create_qmm(self):
            ...     from qm.octave import QmOctaveConfig
            ...     octave_config = QmOctaveConfig()
            ...     octave_config.add_device_info('oct1', ip, port)
            ...     return QuantumMachinesManager(
            ...         host=self.opx_metadata.host_ip,
            ...         port=self.opx_metadata.port,
            ...         cluster_name=self.opx_metadata.cluster_name,
            ...         octave=octave_config
            ...     )
        """
        return QuantumMachinesManager(
            host=self.opx_metadata.host_ip,
            port=self.opx_metadata.port,
            cluster_name=self.opx_metadata.cluster_name,
        )

    def _build_program(self):
        """Build QUA program from callable.

        Returns:
            QUA program object.
        """
        with program() as prog:
            self.program_callable()
        return prog

    def open(self) -> OPXManagerAndMachine:
        """Open QuantumMachine with stored configuration.

        Override to customize opening behavior (e.g., config validation).

        Returns:
            OPXManagerAndMachine with manager and machine references.

        Raises:
            OpenQmException: If QM fails to open.
        """
        qmm = self.get_or_create_qmm()
        qm = qmm.open_qm(self.config, close_other_machines=True)
        return OPXManagerAndMachine(manager=qmm, machine=qm)

    def execute(self, manager_and_machine: OPXManagerAndMachine) -> OPXContext:
        """Execute program on hardware.

        Args:
            manager_and_machine: Opened hardware connection from open().

        Returns:
            OPXContext: Context with job and result handles.
        """
        prog = self._build_program()
        job = manager_and_machine.machine.execute(prog)

        self._context = OPXContext(
            manager=manager_and_machine.manager,
            qm=manager_and_machine.machine,
            job=job,
            result_handles=job.result_handles,
        )
        return self._context

    def create_qua_script(self) -> str:
        """Generate QUA script string from the program.

        Returns:
            QUA script as a string for debugging or inspection.
        """
        return generate_qua_script(self._build_program(), self.config)

    def simulate(
        self,
        manager_and_machine: OPXManagerAndMachine,
        duration_ns: int,
        flags: list[str] | None = None,
        simulation_interface=None
    ) -> SimulationData:
        """Simulate program without hardware execution.

        Args:
            manager_and_machine: Opened hardware connection from open().
            duration_ns: Simulation duration in nanoseconds.
            flags: Optional simulation flags.
            simulation_interface: Optional QM simulation interface.

        Returns:
            SimulationData: Results from QM simulator.
        """
        prog = self._build_program()
        duration_cycles = ns_to_clock_cycles(duration_ns)

        return simulate_program(
            manager_and_machine.manager,
            self.config,
            prog,
            duration_cycles,
            flags or [],
            simulation_interface
        )

    def close(self, manager_and_machine: OPXManagerAndMachine | None = None) -> None:
        """Close the current QuantumMachine.

        Args:
            manager_and_machine: Connection to close. If None, uses stored connection.

        Override to customize closing behavior (e.g., keep-open logic).

        Raises:
            QmFailedToCloseQuantumMachineError: If QM fails to close.
        """
        mm = manager_and_machine or self._manager_and_machine
        if mm is not None:
            mm.machine.close()
            self._manager_and_machine = None

    @property
    def context(self) -> OPXContext:
        """Get current execution context.

        Returns:
            OPXContext from most recent execute() call.

        Raises:
            ValueError: If execute() hasn't been called yet.
        """
        if self._context is None:
            raise ValueError("Context not available. Call execute() first.")
        return self._context
