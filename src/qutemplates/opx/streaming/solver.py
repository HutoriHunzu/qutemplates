"""
Streaming strategy solver - builds workflows for StreamingOPX experiments.

Note: User will implement streaming strategies.
This file provides the structure and placeholders.
"""

from typing import Literal
from quflow import Workflow

from .interface import StreamingInterface

# Type alias for streaming strategies
StreamingStrategy = Literal[
    "wait_for_all", "wait_for_progress", "live_plotting", "live_plotting_with_progress"
]


def solve_strategy(strategy: StreamingStrategy, interface: StreamingInterface) -> Workflow:
    """
    Solve streaming strategy and return workflow.

    TODO: User to implement streaming strategy builders.

    Args:
        strategy: Strategy name
        interface: StreamingInterface with experiment methods

    Returns:
        Configured workflow

    Raises:
        NotImplementedError: Streaming strategies not yet implemented
    """
    raise NotImplementedError(
        f"Streaming strategies not yet implemented. "
        f"User will implement strategy '{strategy}' separately."
    )
