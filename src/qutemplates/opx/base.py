"""Minimal contract for OPX experiment templates."""

from __future__ import annotations

from abc import ABC, abstractmethod

from qm import FullQuaConfig
from qm.qua import program

from .context import OPXContext
from .handler import BaseOpxHandler


class BaseOPX(ABC):
    """Abstract base for OPX experiment templates.

    Templates own their execution semantics and control the full lifecycle:
    open -> execute/simulate -> close.

    Implement define_program() and construct_opx_handler().
    """

    # Subclasses must define these
    config: FullQuaConfig

    def __init__(self) -> None:
        self._opx_handler: BaseOpxHandler | None = None
        self._opx_context: OPXContext | None = None

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
        """Current execution context. Available after handler.execute()."""
        if self._opx_context is None:
            raise ValueError("Context not available. Call handler.execute() first.")
        return self._opx_context

    @opx_context.setter
    def opx_context(self, value: OPXContext):
        self._opx_context = value

    def _build_program(self):
        """Build QUA program from define_program()."""
        with program() as prog:
            self.define_program()
        return prog

    def create_qua_script(self) -> str:
        """Generate QUA script string from the program."""
        return self.opx_handler.generate_qua_script(self._build_program())
