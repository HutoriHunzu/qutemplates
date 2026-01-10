"""Default OPX handler with shared QMM per IP address."""

from __future__ import annotations

from qm import FullQuaConfig, QuantumMachinesManager, generate_qua_script

from ..context import OPXContext, OPXManagerAndMachine
from ..simulation import SimulationData, simulate_program
from .base import BaseOpxHandler


class DefaultOpxHandler(BaseOpxHandler):
    """Default OPX handler with shared QMM per IP address.

    Caches QMM per IP to avoid reconnection overhead.
    Override create_qmm() for custom manager creation (e.g., with Octave).
    """

    _ip_to_manager: dict[str, QuantumMachinesManager] = {}

    def __init__(self, opx_metadata, config: FullQuaConfig):
        self.opx_metadata = opx_metadata
        self.config = config
        self._manager_and_machine: OPXManagerAndMachine | None = None

    @property
    def manager_and_machine(self) -> OPXManagerAndMachine:
        if self._manager_and_machine is None:
            raise ValueError("Manager and machine are not set, use open first")
        return self._manager_and_machine

    def get_or_create_qmm(self) -> QuantumMachinesManager:
        """Get or create QMM for this IP. Shared across handlers."""
        ip = self.opx_metadata.host_ip
        if ip not in self._ip_to_manager:
            self._ip_to_manager[ip] = self.create_qmm()
        return self._ip_to_manager[ip]

    def create_qmm(self) -> QuantumMachinesManager:
        """Create new QMM. Override to customize (e.g., add Octave config)."""
        return QuantumMachinesManager(
            host=self.opx_metadata.host_ip,
            port=self.opx_metadata.port,
            cluster_name=self.opx_metadata.cluster_name,
        )

    def open(self):
        """Open QuantumMachine with stored configuration."""
        qmm = self.get_or_create_qmm()
        qm = qmm.open_qm(self.config, close_other_machines=True)
        self._manager_and_machine = OPXManagerAndMachine(manager=qmm, machine=qm)

    def execute(self, program) -> OPXContext:
        """Execute program and return context."""
        mm = self.manager_and_machine
        job = mm.machine.execute(program)
        return OPXContext(
            manager=mm.manager,
            qm=mm.machine,
            job=job,
            result_handles=job.result_handles,
        )

    def simulate(
        self,
        program,
        duration_cycles: int,
        flags: list[str] | None = None,
        simulation_interface=None,
    ) -> SimulationData:
        """Simulate program and return data."""
        mm = self.manager_and_machine
        return simulate_program(
            mm.manager,
            self.config,
            program,
            duration_cycles,
            flags or [],
            simulation_interface,
        )

    def close(self) -> None:
        """Close the QuantumMachine."""
        if self._manager_and_machine is not None:
            self.manager_and_machine.machine.close()
            self._manager_and_machine = None

    def generate_qua_script(self, program) -> str:
        return generate_qua_script(program, self.config)
