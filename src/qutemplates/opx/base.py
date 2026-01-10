"""Minimal contract for OPX experiment templates."""

from __future__ import annotations

from abc import ABC, abstractmethod

from qutemplates.opx.handler.opx_context import OPXContext

from .handler import BaseOpxHandler


class BaseOPX(ABC):
    """Abstract base for OPX experiment templates.

    Templates own their execution semantics. Implement define_program()
    and construct_opx_handler(). Templates provide their own execute()
    and simulate() methods.
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

    @property
    def opx_context(self) -> OPXContext:
        return self.opx_handler.context

