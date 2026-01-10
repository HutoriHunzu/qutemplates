"""Minimal contract for OPX experiment templates."""

from __future__ import annotations

from abc import ABC, abstractmethod

from qm import FullQuaConfig, generate_qua_script
from qm.qua import program

from .context import OPXContext, OPXManagerAndMachine
from .handler import BaseOpxHandler
from .simulation import SimulationData, simulate_program
from .utils import ns_to_clock_cycles


class BaseOPX(ABC):
    """Abstract base for OPX experiment templates.

    Templates own their execution semantics. Implement define_program()
    and construct_opx_handler().

    Execution and simulation logic is provided by this base class.
    Handlers only manage hardware lifecycle (open/close).
    """

    # Subclasses must define these
    config: FullQuaConfig

    def __init__(self) -> None:
        self._opx_handler: BaseOpxHandler | None = None
        self._context: OPXContext | None = None
        self._manager_and_machine: OPXManagerAndMachine | None = None

    @abstractmethod
    def define_program(self) -> None:
        """Define QUA program (called within program context)."""

    @abstractmethod
    def construct_opx_handler(self) -> BaseOpxHandler:
        """Construct OPX handler for hardware lifecycle management."""

    @property
    def opx_handler(self) -> BaseOpxHandler:
        """Lazily constructed OPX handler."""
        if self._opx_handler is None:
            self._opx_handler = self.construct_opx_handler()
        return self._opx_handler

    @property
    def opx_context(self) -> OPXContext:
        """Current execution context. Available after execute_program()."""
        if self._context is None:
            raise ValueError("Context not available. Call execute_program() first.")
        return self._context

    def _build_program(self):
        """Build QUA program from define_program()."""
        with program() as prog:
            self.define_program()
        return prog

    def create_qua_script(self) -> str:
        """Generate QUA script string from the program."""
        return generate_qua_script(self._build_program(), self.config)

    def execute_program(self) -> OPXContext:
        """Open hardware, execute program, and return context.

        The context is stored and accessible via opx_context property.
        Call close() when done to release hardware.

        Returns:
            OPXContext: Execution context with job and result handles.
        """
        mm = self.opx_handler.open()
        self._manager_and_machine = mm
        prog = self._build_program()
        job = mm.machine.execute(prog)
        self._context = OPXContext(
            manager=mm.manager,
            qm=mm.machine,
            job=job,
            result_handles=job.result_handles,
        )
        return self._context

    def _run_simulation(
        self,
        duration_ns: int,
        flags: list[str] | None = None,
        simulation_interface=None,
    ) -> SimulationData:
        """Run simulation and return data.

        Opens hardware, simulates program, closes connection.

        Args:
            duration_ns: Simulation duration in nanoseconds.
            flags: Optional simulation flags.
            simulation_interface: Optional QM simulation interface.

        Returns:
            SimulationData: Results from QM simulator.
        """
        mm = self.opx_handler.open()
        try:
            prog = self._build_program()
            duration_cycles = ns_to_clock_cycles(duration_ns)
            return simulate_program(
                mm.manager, self.config, prog, duration_cycles, flags or [], simulation_interface
            )
        finally:
            self.opx_handler.close(mm)

    def close(self) -> None:
        """Close the hardware connection."""
        self.opx_handler.close(self._manager_and_machine)
        self._manager_and_machine = None
