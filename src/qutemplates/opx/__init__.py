"""OPX-specific experiment implementation."""

# New experiment class hierarchy (RECOMMENDED)
from .base_experiment import BaseExperiment
from .batch_experiment import BatchExperiment
from .streaming_experiment import StreamingExperiment
from .interactive_experiment import InteractiveExperiment

# Backward compatibility - OpxExperiment shim with delegation to old API
import warnings
from abc import abstractmethod
from typing import TypeVar


T = TypeVar('T')


class OpxExperiment(BatchExperiment[T]):
    """
    Deprecated: Use BatchExperiment instead.

    OpxExperiment is maintained for backward compatibility but is deprecated.
    This class implements the old API (fetch_results + post_run with data arg)
    and delegates to the new BatchExperiment implementation.

    Old experiments that implement fetch_results() and post_run(data) will
    continue to work without modification.

    New code should use:
    - BatchExperiment: For fetch-all semantics (most common)
    - StreamingExperiment: For incremental chunk semantics
    - InteractiveExperiment: For point-by-point evaluation

    This class will be removed in a future major version.
    """

    def __init__(self):
        warnings.warn(
            "OpxExperiment is deprecated. Use BatchExperiment, StreamingExperiment, "
            "or InteractiveExperiment instead. See migration guide for details.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()

    # ==================== Old API (users implement these) ====================

    @abstractmethod
    def fetch_results(self, **kwargs):
        """
        Old API: Fetch results from hardware.

        This is the legacy method name. New code should use fetch_all_results().

        Returns:
            Raw data from hardware
        """
        pass

    @abstractmethod
    def post_run(self, data) -> T:
        """
        Old API: Process fetched data.

        This is the legacy method name for data processing.
        New code should use process_results().

        Args:
            data: Raw data from fetch_results()

        Returns:
            Processed data

        Note:
            Old contract required saving to self.data AND returning.
            This shim handles both automatically.
        """
        pass

    # ==================== New API (implemented by delegation) ====================

    def fetch_all_results(self):
        """Shim: Delegates to legacy fetch_results()."""
        return self.fetch_results()

    def process_results(self, raw) -> T:
        """
        Shim: Delegates to legacy post_run().

        The old post_run() contract required both saving to self.data
        and returning the result. We call it and return the result.
        The framework will save to self.data again (harmless double-save).
        """
        result = self.post_run(raw)
        return result


# Keep old imports for backward compatibility
from .base import OpxExperiment as _OldOpxExperiment  # Old implementation
from qutemplates.opx.hardware.opx_handler import OPXHandler
from .node_names import OPXNodeName
from .execution_strategy import OPXExecutionStrategy
from .execution_mode import ExecutionMode
from .experiment_interface import ExperimentInterface
from .strategies import solve_strategy
from .hardware import Averager

__all__ = [
    # New API (RECOMMENDED)
    'BaseExperiment',
    'BatchExperiment',
    'StreamingExperiment',
    'InteractiveExperiment',

    # Backward compatibility (DEPRECATED)
    'OpxExperiment',

    # Supporting classes
    'OPXHandler',
    'OPXNodeName',
    'OPXExecutionStrategy',
    'ExecutionMode',
    'ExperimentInterface',
    'solve_strategy',
    'Averager'
]
