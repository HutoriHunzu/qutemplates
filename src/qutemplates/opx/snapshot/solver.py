"""
Snapshot strategy solver - builds workflows for SnapshotOPX experiments.

Strategies:
- 'wait_for_all': Only job polling (minimal)
- 'wait_for_progress': Job polling + progress bar
- 'live_plotting': Job polling + data acquisition + live animation
- 'live_plotting_with_progress': All features (full-featured)
"""

from typing import Literal

from quflow import Workflow

from ..shared.components import (
    add_live_animation,
    create_job_polling,
    create_progress_bar,
)
from .data_acquisition import create_fetch_post_skeleton
from .interface import SnapshotInterface

# Type alias for snapshot strategies
SnapshotStrategy = Literal[
    "wait_for_all", "wait_for_progress", "live_plotting", "live_plotting_with_progress"
]


def solve_strategy(strategy: SnapshotStrategy, interface: SnapshotInterface) -> Workflow:
    """
    Solve snapshot strategy and return workflow.

    Args:
        strategy: Strategy name (Literal for easy specification)
        interface: SnapshotInterface with experiment methods

    Returns:
        Configured workflow

    Raises:
        ValueError: If strategy name not found

    Example:
        >>> interface = SnapshotInterface(...)
        >>> workflow = solve_strategy('live_plotting_with_progress', interface)
        >>> workflow.execute()
    """
    builder = STRATEGY_REGISTRY.get(strategy)

    if builder is None:
        available = list(STRATEGY_REGISTRY.keys())
        raise ValueError(f"Unknown snapshot strategy: '{strategy}'. Available: {available}")

    return builder(interface)


# Strategy builder functions


def build_wait_for_all(interface: SnapshotInterface) -> Workflow:
    """
    wait_for_all: Only job polling (no data acquisition during workflow).

    Minimal workflow - just waits for OPX job completion.
    Template will do final fetch/post after workflow.
    """
    flow = Workflow()
    create_job_polling(flow, interface.opx_context)
    return flow


def build_wait_for_progress(interface: SnapshotInterface) -> Workflow:
    """
    wait_for_progress: Job polling + progress bar.

    Shows progress during execution but no live data updates.

    Raises:
        ValueError: If averager_interface is None (progress requires averaging)
    """
    if interface.averager_interface is None:
        raise ValueError(
            "Strategy 'wait_for_progress' requires averaging to be enabled. "
            "Use an Averager in your experiment or choose a different strategy."
        )

    flow = Workflow()
    create_job_polling(flow, interface.opx_context)
    create_progress_bar(flow, interface.averager_interface)
    return flow


def build_live_plotting(interface: SnapshotInterface) -> Workflow:
    """
    live_plotting: Job polling + data acquisition + live animation.

    Full data pipeline with live updates but no progress bar.

    Raises:
        ValueError: If live_plotting interface is None (methods not implemented)
    """
    if interface.live_plotting is None:
        raise ValueError(
            "Strategy 'live_plotting' requires setup_plot() and update_plot() "
            "to be implemented in your experiment class."
        )

    flow = Workflow()
    post_node = create_fetch_post_skeleton(flow, interface)
    create_job_polling(flow, interface.opx_context)
    add_live_animation(
        flow,
        post_node,
        interface.live_plotting.setup_plot,
        interface.live_plotting.update_plot,
        interface.live_plotting.averager_interface,
    )
    return flow


def build_live_plotting_with_progress(interface: SnapshotInterface) -> Workflow:
    """
    live_plotting_with_progress: All features.

    Complete feature set: data pipeline, job polling, progress, live plots.
    This is the full-featured/standard strategy.

    Raises:
        ValueError: If live_plotting or averager_interface is None
    """
    if interface.live_plotting is None:
        raise ValueError(
            "Strategy 'live_plotting_with_progress' requires setup_plot() and update_plot() "
            "to be implemented in your experiment class."
        )

    if interface.averager_interface is None:
        raise ValueError(
            "Strategy 'live_plotting_with_progress' requires averaging to be enabled. "
            "Use an Averager in your experiment."
        )

    flow = Workflow()
    post_node = create_fetch_post_skeleton(flow, interface)
    create_job_polling(flow, interface.opx_context)
    create_progress_bar(flow, interface.averager_interface)
    add_live_animation(
        flow,
        post_node,
        interface.live_plotting.setup_plot,
        interface.live_plotting.update_plot,
        interface.live_plotting.averager_interface,
    )
    return flow


# Registry mapping strategy names to builders
STRATEGY_REGISTRY = {
    "wait_for_all": build_wait_for_all,
    "wait_for_progress": build_wait_for_progress,
    "live_plotting": build_live_plotting,
    "live_plotting_with_progress": build_live_plotting_with_progress,
}
