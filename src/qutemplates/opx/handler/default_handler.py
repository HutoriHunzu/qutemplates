"""Default OPX hardware handler implementation."""

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
    """Default OPX hardware handler implementation.

    Features:
    - Shared QMM per IP address (class-level caching)
    - Standard QM lifecycle
    - Program building from callable
    - Support for both execution and simulation

    State Management:
    - QMM: Shared per IP address via class-level dict
    - Config: Stored at construction time
    - Program callable: Stored at construction time
    - Context: Created after execute(), available via context property

    Extensibility:
    - Override create_qmm() for custom manager creation (e.g., with octave)
    - Override open() for custom QM opening logic
    - Override close() for custom closing logic (e.g., keep-alive)

    Example - Basic usage:
        >>> handler = DefaultOpxHandler(metadata, config, my_program)
        >>> mm = handler.open()
        >>> ctx = handler.execute(mm)
        >>> data = ctx.result_handles.get('I').fetch_all()
        >>> handler.close()

    Example - Custom keep-alive:
        >>> class KeepOpenHandler(DefaultOpxHandler):
        ...     def close(self):
        ...         if not self.auto_close:
        ...             return
        ...         super().close()
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
            OPXContext with job, result handles, and debug script.
        """
        manager, machine = manager_and_machine.manager, manager_and_machine.machine

        # Build program
        prog = self._build_program()

        # Execute
        job = machine.execute(prog)

        # Create and store context
        self._context = OPXContext(
            manager=manager,
            qm=machine,
            job=job,
            result_handles=job.result_handles,
        )

        return self._context

    def create_qua_scirpt(self) -> str:
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
            Simulation data from QM simulator.
        """
        # Build program
        prog = self._build_program()

        # Convert duration and run simulation
        duration_cycles = ns_to_clock_cycles(duration_ns)

        return simulate_program(
            manager_and_machine.manager,
            self.config,
            prog,
            duration_cycles,
            flags or [],
            simulation_interface
        )

    def close(self, manager_and_machine: OPXManagerAndMachine) -> None:
        """Close the current QuantumMachine.

        Override to customize closing behavior (e.g., keep-open logic).

        Raises:
            QmFailedToCloseQuantumMachineError: If QM fails to close.
        """
        manager_and_machine.machine.close()

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
