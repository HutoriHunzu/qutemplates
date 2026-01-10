"""Minimal contract for OPX experiment templates."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .handler import BaseOpxHandler
from .simulation import SimulationData


class BaseOPX(ABC):
    """Abstract base for OPX experiment templates.

    Templates own their execution semantics:
    - SnapshotOPX: Fetch all accumulated data at once
    - StreamingOPX: Incremental chunk-based data fetching
    - InteractiveOPX: Point-by-point evaluation for optimization
    """

    def __init__(self) -> None:
        self._opx_handler: BaseOpxHandler | None = None

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

    def simulate(
        self,
        duration_ns: int,
        debug_path: str | None = None,
        auto_element_thread: bool = False,
        not_strict_timing: bool = False,
        simulation_interface=None,
    ) -> SimulationData:
        """Simulate program without hardware execution.

        Args:
            duration_ns: Simulation duration in nanoseconds.
            debug_path: Optional path to save QUA debug script.
            auto_element_thread: Enable auto-element-thread simulation flag.
            not_strict_timing: Enable not-strict-timing simulation flag.
            simulation_interface: Optional QM simulation interface.

        Returns:
            SimulationData from QM simulator.
        """
        flags: list[str] = []
        if auto_element_thread:
            flags.append("auto-element-thread")
        if not_strict_timing:
            flags.append("not-strict-timing")

        data = self.opx_handler.open_and_simulate(
            duration_ns, flags, simulation_interface
        )

        if debug_path:
            with open(debug_path, "w") as f:
                f.write(self.opx_handler.create_qua_script())

        return data
