"""
Minimal strategy - FETCH → POST only.

This is the most basic OPX execution strategy with no additional features.
Just data acquisition and post-processing, nothing else.

Use when:
- Maximum simplicity needed
- Custom features will be added manually
- Debugging basic workflow
- Complete control over execution
"""

from typing import Tuple
from quflow import Workflow

from ..execution_mode import ExecutionMode
from ..experiment_interface import ExperimentInterface
from .components import select_data_acquisition_component


def build_minimal(
    interface: ExperimentInterface,
    execution_mode: ExecutionMode
) -> Workflow:
    """
    Build minimal strategy workflow: FETCH → POST only.

    Creates the most basic workflow with just data acquisition and processing.
    No job polling, no progress bar, no live plotting.

    This is truly minimal - use STANDARD strategy if you want the full feature set.

    Args:
        interface: Experiment interface with fetch_results and post_run
        execution_mode: Execution mode controlling data acquisition pattern

    Returns:
        Configured workflow with minimal pipeline

    Note:
        Without job polling, the FETCH and POST nodes will poll indefinitely
        until manually interrupted or the workflow times out. This strategy
        is best used when you have custom control logic or for debugging.

        Final fetch behavior is inherent to experiment type:
        - BatchExperiment: Always does final fetch
        - StreamingExperiment: Never does final fetch
    """
    flow = Workflow()

    # Select data acquisition component based on execution mode
    create_data_acquisition, _needs_final_fetch = select_data_acquisition_component(execution_mode)

    # Create core pipeline only (mode-dependent)
    post_node = create_data_acquisition(flow, interface)

    return flow
