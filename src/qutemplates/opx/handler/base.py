"""Abstract handler for OPX hardware lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod

from qm import FullQuaConfig

from ..context import OPXContext, OPXManagerAndMachine
from ..simulation import SimulationData


class BaseOpxHandler(ABC):
    """Abstract base class for OPX hardware handlers.

    Handlers manage the full hardware lifecycle: open, execute/simulate, close.
    """

    @abstractmethod
    def __init__(self, opx_metadata, config: FullQuaConfig):
        """Initialize handler with metadata and config."""
        pass

    @abstractmethod
    def open(self) -> OPXManagerAndMachine:
        """Open connection to quantum hardware."""
        pass

    @abstractmethod
    def execute(self, program) -> OPXContext:
        """Execute program and return context. Call open() first."""
        pass

    @abstractmethod
    def simulate(
        self,
        program,
        duration_cycles: int,
        flags: list[str] | None = None,
        simulation_interface=None,
    ) -> SimulationData:
        """Simulate program and return data. Call open() first."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connection to quantum hardware."""
        pass
