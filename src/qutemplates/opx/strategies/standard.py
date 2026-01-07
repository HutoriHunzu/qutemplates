"""
Standard strategy - full-featured OPX workflow.

This is the recommended strategy for most OPX experiments. It includes
all standard features: data acquisition, job monitoring, progress tracking,
and live plotting.

Use when:
- Running standard experiments
- Want real-time feedback (progress bar, live plots)
- Need complete feature set out of the box
"""

from quflow import Workflow

from ..execution_mode import ExecutionMode
from ..experiment_interface import ExperimentInterface
from .components import (
    create_job_polling,
    create_progress_bar,
    add_live_animation,
    select_data_acquisition_component
)


def build_standard(
        interface: ExperimentInterface,
        execution_mode: ExecutionMode
) -> Workflow:
    """
    Build standard strategy workflow with all features.

    Includes:
    - FETCH → POST pipeline (mode-dependent: standard vs streaming)
    - Job status polling (monitors completion, sets interrupt)
    - Progress bar (shows averaging progress via Averager)
    - Live animation (real-time plotting)

    This is the recommended strategy for most experiments - it provides
    complete functionality with real-time feedback.

    Args:
        interface: Experiment interface with all required callables
        execution_mode: Execution mode controlling data acquisition pattern

    Returns:
        Configured workflow with all features

    Note:
        All features run in parallel. Job polling coordinates graceful
        shutdown by setting an interrupt when the OPX job completes,
        which stops all ConditionPollingTasks (FETCH, POST, PROGRESS).

        Final fetch behavior is inherent to experiment type:
        - BatchExperiment: Always does final fetch
        - StreamingExperiment: Never does final fetch
    """
    flow = Workflow()

    # Select data acquisition component based on execution mode
    create_data_acquisition, _needs_final_fetch = select_data_acquisition_component(execution_mode)

    # Core data pipeline (mode-dependent)
    post_node = create_data_acquisition(flow, interface)

    # Job monitoring (sets interrupt when done)
    create_job_polling(flow, interface)

    # Progress tracking
    create_progress_bar(flow, interface)

    # Live plotting
    add_live_animation(flow, post_node, interface)

    return flow
