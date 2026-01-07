"""
Batch strategy solver - builds workflows for BatchOPX experiments.

Strategies:
- 'wait_for_all': Only job polling (minimal)
- 'wait_for_progress': Job polling + progress bar
- 'live_plotting': Job polling + data acquisition + live animation
- 'live_plotting_with_progress': All features (full-featured)
"""

from typing import Literal
from quflow import Workflow

from .interface import BatchInterface
from ..shared.components import (
    create_job_polling,
    create_progress_bar,
    add_live_animation
)
from .components import create_fetch_post_skeleton

# Type alias for batch strategies
BatchStrategy = Literal[
    'wait_for_all',
    'wait_for_progress',
    'live_plotting',
    'live_plotting_with_progress'
]


def solve_strategy(strategy: BatchStrategy, interface: BatchInterface) -> Workflow:
    """
    Solve batch strategy and return workflow.

    Args:
        strategy: Strategy name (Literal for easy specification)
        interface: BatchInterface with experiment methods

    Returns:
        Configured workflow

    Raises:
        ValueError: If strategy name not found

    Example:
        >>> interface = BatchInterface(...)
        >>> workflow = solve_strategy('live_plotting_with_progress', interface)
        >>> workflow.execute()
    """
    builder = STRATEGY_REGISTRY.get(strategy)

    if builder is None:
        available = list(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown batch strategy: '{strategy}'. "
            f"Available: {available}"
        )

    return builder(interface)


# Strategy builder functions

def build_wait_for_all(interface: BatchInterface) -> Workflow:
    """
    wait_for_all: Only job polling (no data acquisition during workflow).

    Minimal workflow - just waits for OPX job completion.
    Template will do final fetch/post after workflow.
    """
    flow = Workflow()
    create_job_polling(flow, interface)
    return flow


def build_wait_for_progress(interface: BatchInterface) -> Workflow:
    """
    wait_for_progress: Job polling + progress bar.

    Shows progress during execution but no live data updates.
    """
    flow = Workflow()
    create_job_polling(flow, interface)
    create_progress_bar(flow, interface)
    return flow


def build_live_plotting(interface: BatchInterface) -> Workflow:
    """
    live_plotting: Job polling + data acquisition + live animation.

    Full data pipeline with live updates but no progress bar.
    """
    flow = Workflow()
    post_node = create_fetch_post_skeleton(flow, interface)
    create_job_polling(flow, interface)
    add_live_animation(flow, post_node, interface)
    return flow


def build_live_plotting_with_progress(interface: BatchInterface) -> Workflow:
    """
    live_plotting_with_progress: All features.

    Complete feature set: data pipeline, job polling, progress, live plots.
    This is the full-featured/standard strategy.
    """
    flow = Workflow()
    post_node = create_fetch_post_skeleton(flow, interface)
    create_job_polling(flow, interface)
    create_progress_bar(flow, interface)
    add_live_animation(flow, post_node, interface)
    return flow


# Registry mapping strategy names to builders
STRATEGY_REGISTRY = {
    'wait_for_all': build_wait_for_all,
    'wait_for_progress': build_wait_for_progress,
    'live_plotting': build_live_plotting,
    'live_plotting_with_progress': build_live_plotting_with_progress,
}
