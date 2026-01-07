"""
New solver with type-based dispatch for multiple experiment types.

This solver uses interface type (BatchInterface vs StreamingInterface) to
dispatch to the appropriate builder function, instead of using ExecutionMode.

Architecture:
- SOLVER_REGISTRY maps interface type → builder function
- solve_strategy() dispatches based on type(interface)
- Each builder constructs workflow for its experiment type
- Shared components (job polling, progress, live plot) reused
- Only data acquisition component differs between types
"""

from quflow import Workflow

from ..execution_strategy import OPXExecutionStrategy
from ..batch.interface import BatchInterface
from ..streaming.interface import StreamingInterface

# Import actual builders
from .batch_builders import build_batch_standard, build_batch_minimal
from .streaming_builders import build_streaming_standard, build_streaming_minimal


# Type-based registry - maps interface class to builder mapping
# Each interface type has its own strategy registry
BATCH_STRATEGY_REGISTRY = {
    OPXExecutionStrategy.STANDARD: build_batch_standard,
    OPXExecutionStrategy.MINIMAL: build_batch_minimal,
}

STREAMING_STRATEGY_REGISTRY = {
    OPXExecutionStrategy.STANDARD: build_streaming_standard,
    OPXExecutionStrategy.MINIMAL: build_streaming_minimal,
}

# Master registry mapping interface type to strategy registry
SOLVER_REGISTRY = {
    BatchInterface: BATCH_STRATEGY_REGISTRY,
    StreamingInterface: STREAMING_STRATEGY_REGISTRY,
}


def solve_strategy(
    strategy: OPXExecutionStrategy,
    interface: BatchInterface | StreamingInterface
) -> Workflow:
    """
    Solve strategy using type-based dispatch.

    Dispatches to appropriate builder based on interface type:
    - BatchInterface → batch strategy builders
    - StreamingInterface → streaming strategy builders

    Args:
        strategy: Execution strategy enum (STANDARD, MINIMAL, etc.)
        interface: Experiment interface (type determines dispatch)

    Returns:
        Constructed workflow

    Raises:
        TypeError: If interface type not recognized
        KeyError: If strategy not implemented for interface type

    Example:
        >>> interface = BatchInterface(...)
        >>> workflow = solve_strategy(OPXExecutionStrategy.STANDARD, interface)
        >>> workflow.execute()
    """
    # Get interface type
    interface_type = type(interface)

    # Look up strategy registry for this interface type
    if interface_type not in SOLVER_REGISTRY:
        raise TypeError(
            f"Unknown interface type: {interface_type}. "
            f"Supported types: {list(SOLVER_REGISTRY.keys())}"
        )

    strategy_registry = SOLVER_REGISTRY[interface_type]

    # Look up builder for this strategy
    if strategy not in strategy_registry:
        raise KeyError(
            f"Strategy {strategy} not implemented for {interface_type.__name__}"
        )

    builder = strategy_registry[strategy]
    if builder is None:
        raise NotImplementedError(
            f"Strategy {strategy} for {interface_type.__name__} not yet implemented"
        )

    # Build and return workflow
    return builder(interface)
