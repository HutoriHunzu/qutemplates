"""Caching OPX handler with machine reuse based on config hash."""

from __future__ import annotations

from qm import FullQuaConfig, QuantumMachine, QuantumMachinesManager, generate_qua_script

from ..context import OPXContext, OPXManagerAndMachine
from ..simulation import SimulationData, simulate_program
from .base import BaseOpxHandler


class CachingOpxHandler(BaseOpxHandler):
    """Handler that caches machines by IP + physical config hash.

    Avoids reopening machines when the physical configuration hasn't changed.
    Splits config into logical and physical parts, using the physical part
    for cache lookup.

    Override _split_config() and _hash_config() to implement config handling.
    """

    # Class-level caches
    _ip_to_manager: dict[str, QuantumMachinesManager] = {}
    _cache: dict[tuple[str, str], QuantumMachine] = {}

    def __init__(
        self,
        opx_metadata,
        config: FullQuaConfig,
        close_on_close: bool = False,
    ):
        """Initialize handler.

        Args:
            close_on_close: If True, close() removes machine from cache.
        """
        self.opx_metadata = opx_metadata
        self.config = config
        self.close_on_close = close_on_close
        self._logical_config: dict | None = None
        self._physical_config: dict | None = None
        self._cache_key: tuple[str, str] | None = None
        self._manager_and_machine: OPXManagerAndMachine | None = None

    def _split_config(self, config: FullQuaConfig) -> tuple[dict, dict]:
        """Split config into logical and physical parts. Override in subclass."""
        raise NotImplementedError("Subclass must implement _split_config()")

    def _hash_config(self, physical_config: dict) -> str:
        """Hash physical config for cache key. Override in subclass."""
        raise NotImplementedError("Subclass must implement _hash_config()")

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

    @property
    def manager_and_machine(self) -> OPXManagerAndMachine:
        if self._manager_and_machine is None:
            raise ValueError('Manager and machine are not set, use open first')
        return self._manager_and_machine

    def open(self):
        """Open or retrieve cached QuantumMachine based on config hash."""
        self._logical_config, self._physical_config = self._split_config(self.config)
        config_hash = self._hash_config(self._physical_config)
        self._cache_key = (self.opx_metadata.host_ip, config_hash)

        qmm = self.get_or_create_qmm()

        if self._cache_key in self._cache:
            machine = self._cache[self._cache_key]
        else:
            machine = qmm.open_qm(self._physical_config, close_other_machines=False)
            self._cache[self._cache_key] = machine

        self._manager_and_machine = OPXManagerAndMachine(manager=qmm, machine=machine)

    def _get_execute_kwargs(self) -> dict:
        """Get kwargs for machine.execute() from logical config."""
        return self._logical_config or {}

    def execute(self, program) -> OPXContext:
        """Execute program with logical config kwargs."""
        mm = self.manager_and_machine
        job = mm.machine.execute(program, **self._get_execute_kwargs())
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
            self._physical_config or self.config,
            program,
            duration_cycles,
            flags or [],
            simulation_interface,
        )

    def close(self) -> None:
        """Close machine if close_on_close is True, otherwise keep cached."""
        if not self.close_on_close:
            return

        if self._cache_key and self._cache_key in self._cache:
            machine = self._cache.pop(self._cache_key)
            machine.close()


    def generate_qua_script(self, program) -> str:
        return generate_qua_script(program, self.config)
