"""
OPX hardware layer - low-level hardware operations.

This package contains hardware-level operations that are separate from
experiment-level orchestration. This separation allows:
- A single OPXHandler to orchestrate multiple experiments in series
- Explicit state management via interfaces
- Reuse of hardware operations in non-experiment contexts
- Direct access to simulation without experiment workflow
"""

from .opx_context import OPXContext
from .opx_handler import OPXHandler
from .averager import AveragerInterface, Averager
from .simulation import SimulationData, simulate_program

__all__ = [
    "OPXContext",
    "OPXHandler",
    "Averager",
    "AveragerInterface",
    "SimulationData",
    "simulate_program",
]
