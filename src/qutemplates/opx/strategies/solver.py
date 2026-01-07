"""
Strategy solver - maps execution strategy enum to builder functions.

This module provides the registry and solver that:
1. Maps OPXExecutionStrategy enum values to builder functions
2. Selects data acquisition components based on execution mode
3. Calls the appropriate builder to create the workflow
4. Returns workflow + flag indicating if final fetch is needed
"""

from quflow import Workflow

from ..execution_strategy import OPXExecutionStrategy
from ..execution_mode import ExecutionMode
from ..experiment_interface import ExperimentInterface

from .standard import build_standard
from .minimal import build_minimal
from .with_live_animation import build_with_live_animation
from .minimal_no_live import build_minimal_no_live

from .components.data_acquisition import create_fetch_post_skeleton
from .components.streaming_data_acquisition import create_streaming_fetch_post


# Strategy registry - maps enum to builder function
STRATEGY_REGISTRY = {
    OPXExecutionStrategy.STANDARD: build_standard,
    OPXExecutionStrategy.MINIMAL: build_minimal,
    OPXExecutionStrategy.WITH_LIVE_ANIMATION: build_with_live_animation,
    OPXExecutionStrategy.MINIMAL_NO_LIVE: build_minimal_no_live,
    # More strategies will be added here as they're implemented
}



def solve_strategy(
    strategy: OPXExecutionStrategy,
    interface: ExperimentInterface,
    execution_mode: ExecutionMode = ExecutionMode.STANDARD
) -> Workflow:
    """
    Solve execution strategy and return workflow.

    This is the entry point for workflow construction. Given a strategy
    enum, experiment interface, and execution mode, it:
    1. Looks up the appropriate builder function
    2. Calls the builder with interface and execution mode
    3. Returns the constructed workflow

    Args:
        strategy: Execution strategy enum (controls features: progress, live plot)
        interface: Experiment interface with methods for dependency injection
        execution_mode: Execution mode (controls data acquisition pattern)

    Returns:
        Configured workflow ready for execution

    Raises:
        ValueError: If strategy not found in registry

    Note:
        Final fetch behavior is now inherent to experiment type:
        - BatchExperiment: Always does final fetch after workflow
        - StreamingExperiment: Never does final fetch (data already aggregated)

    Example:
        >>> interface = ExperimentInterface(
        ...     fetch_results=exp.fetch_results,
        ...     post_run=exp.post_run
        ... )
        >>> workflow = solve_strategy(
        ...     OPXExecutionStrategy.STANDARD,
        ...     interface,
        ...     ExecutionMode.STANDARD
        ... )
        >>> workflow.execute()
        >>> # BatchExperiment will do final fetch automatically
    """
    # Look up builder function
    builder = STRATEGY_REGISTRY.get(strategy)

    if builder is None:
        available = list(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown execution strategy: {strategy}. "
            f"Available strategies: {available}"
        )

    # Call builder with interface and execution mode
    workflow = builder(interface, execution_mode)

    return workflow
