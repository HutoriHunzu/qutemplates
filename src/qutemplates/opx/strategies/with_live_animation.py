"""
With Live Animation strategy - FETCH → POST + live plotting.

This strategy adds real-time plotting to the basic data pipeline.
Data flows from POST to LIVE_ANIMATION for visualization during execution.

Use when:
- Need to monitor experiment progress visually
- Want immediate feedback on data quality
- Debugging pulse sequences or calibrations
"""

from quflow import Workflow

from ..execution_mode import ExecutionMode
from ..experiment_interface import ExperimentInterface
from .components import select_data_acquisition_component, add_live_animation


def build_with_live_animation(
    interface: ExperimentInterface,
    execution_mode: ExecutionMode
) -> Workflow:
    """
    Build workflow with live animation: FETCH → POST → LIVE_ANIMATION

    Creates workflow with core data pipeline plus parallel live plotting.
    The POST node feeds data to LIVE_ANIMATION for real-time updates.

    Args:
        interface: Experiment interface with fetch_results, post_run,
                   setup_plot, and update_plot
        execution_mode: Execution mode controlling data acquisition pattern

    Returns:
        Configured workflow with live animation

    Note:
        Unlike STANDARD strategy, this doesn't include job polling or progress.
        Use STANDARD for full feature set.

        Final fetch behavior is inherent to experiment type:
        - BatchExperiment: Always does final fetch
        - StreamingExperiment: Never does final fetch
    """
    flow = Workflow()

    # Select data acquisition component based on execution mode
    create_data_acquisition, _needs_final_fetch = select_data_acquisition_component(execution_mode)

    # Create core pipeline (mode-dependent)
    post_node = create_data_acquisition(flow, interface)

    # Add live animation wired to POST
    add_live_animation(flow, post_node, interface)

    return flow
