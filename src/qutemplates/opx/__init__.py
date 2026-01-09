"""OPX-specific experiment implementation."""

# Import new names
from .snapshot import SnapshotOPX, BatchOPX  # BatchOPX is backward compatibility alias
from .streaming import StreamingOPX
from .interactive import InteractiveOPX
from .hardware import (
    BaseOpxHandler,
    DefaultOpxHandler,
    OPXHandler,
    OPXContext,
    Averager,
)

__all__ = [
    "SnapshotOPX",
    "StreamingOPX",
    "InteractiveOPX",
    "OPXContext",
    "BaseOpxHandler",
    "DefaultOpxHandler",
    "OPXHandler",  # Backward compatibility
    "Averager",
    "BatchOPX",  # Backward compatibility
]
