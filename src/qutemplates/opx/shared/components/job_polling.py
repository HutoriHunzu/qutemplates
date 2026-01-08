from quflow import Workflow, ParallelNode, ContextFuncTask, PollingTask, TaskContext

from ..node_names import OPXNodeName
from ...hardware import OPXContext
from functools import partial


def check_job_is_running_and_set_interrupt(ctx: TaskContext, opx_ctx: OPXContext):
    """
    Create polling function that monitors job status and sets interrupt when done.

    This function creates a closure that continuously checks if the OPX job
    is still processing. When the job completes, it sets the interrupt event
    which signals all ConditionPollingTasks to stop.

    Args:
        opx_ctx: OPX context containing result_handles for status checking

    Returns:
        Callable suitable for ConditionPollingTask that monitors job status

    Note:
        The interrupt mechanism is what allows FETCH, POST, and PROGRESS nodes
        to stop polling once the experiment completes.
    """
    is_running = opx_ctx.result_handles.is_processing()
    if not is_running:
        ctx.interrupt.set()


def create_job_polling(flow: Workflow, opx_context: OPXContext):
    """
    Add job status polling node to workflow.

    Creates a parallel node that continuously monitors whether the OPX job
    is still running. When the job completes, sets an interrupt that stops
    all ConditionPollingTasks in the workflow.

    This is essential for coordinating graceful shutdown of parallel polling
    nodes (FETCH, POST, PROGRESS).

    Args:
        flow: Workflow to add node to
        interface: Experiment interface with opx_context

    Returns:
        Created job polling node

    Note:
        This node should be added to any workflow using ConditionPollingTasks
        to ensure they stop when the experiment completes.
    """

    job_polling = ParallelNode(
        name=OPXNodeName.JOB_STATUS_POLLING,
        task=PollingTask(
            task=ContextFuncTask(
                func=partial(check_job_is_running_and_set_interrupt, opx_ctx=opx_context)
            )
        ),
    )

    flow.add_node(job_polling)

    return job_polling
