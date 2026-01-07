from quflow import Workflow
from .components import create_job_polling, create_progress_bar

def build_minimal_no_live(interface, execution_mode):
    """Build minimal_no_live strategy: job polling only.

    Args:
        interface: Experiment interface
        execution_mode: Execution mode (unused - no data acquisition)

    Returns:
        Workflow with job polling only

    Note:
        Final fetch is handled by experiment type:
        - BatchExperiment: Always does final fetch
        - StreamingExperiment: Never does final fetch
    """
    flow = Workflow()

    create_job_polling(flow, interface)
    # create_progress_bar(flow, interface)

    return flow
