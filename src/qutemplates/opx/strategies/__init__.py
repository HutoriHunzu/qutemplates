"""
OPX execution strategies.

This module provides the strategy pattern for building OPX workflows.
Each strategy is a function that takes an ExperimentInterface, ExecutionMode
and returns a tuple of (Workflow, needs_final_fetch).

Strategies are composable - they reuse component helpers from the components/
subfolder for building workflows.

Available strategies:
- STANDARD: Full-featured workflow (RECOMMENDED) - job polling, progress, live plotting
- MINIMAL: Basic FETCH → POST pipeline only (no features)
- WITH_LIVE_ANIMATION: FETCH → POST + live plotting

Execution modes:
- STANDARD: fetch_all() accumulated data, final fetch after workflow
- STREAMING: fetch(0) incremental chunks, accumulated in memory

More strategies coming soon:
- WITH_PROGRESS: Add progress bar only
- INTERACTIVE: Interactive data acquisition
- etc.
"""

from .solver import solve_strategy, STRATEGY_REGISTRY
from .standard import build_standard
from .minimal import build_minimal
from .with_live_animation import build_with_live_animation

# Component helpers are also available
from .components import (
    create_fetch_post_skeleton,
    create_job_polling,
    create_progress_bar,
    add_live_animation
)
from .components.streaming_data_acquisition import create_streaming_fetch_post

__all__ = [
    # Strategy solver
    'solve_strategy',
    # 'select_data_acquisition_component',
    'STRATEGY_REGISTRY',

    # Strategy builders
    'build_standard',
    'build_minimal',
    'build_with_live_animation',

    # Component helpers (standard mode)
    'create_fetch_post_skeleton',
    'create_job_polling',
    'create_progress_bar',
    'add_live_animation',

    # Component helpers (streaming mode)
    'create_streaming_fetch_post',
]
