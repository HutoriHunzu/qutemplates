"""Snapshot OPX experiments."""

from .template import SnapshotOPX
from .interface import SnapshotInterface
from .solver import SnapshotStrategy, solve_strategy

# Backward compatibility aliases
BatchOPX = SnapshotOPX
BatchInterface = SnapshotInterface
BatchStrategy = SnapshotStrategy

__all__ = [
    "SnapshotOPX",
    "SnapshotInterface",
    "SnapshotStrategy",
    "solve_strategy",
    # Backward compatibility
    "BatchOPX",
    "BatchInterface",
    "BatchStrategy",
]
