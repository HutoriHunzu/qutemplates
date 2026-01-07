"""Job status polling component for OPX strategies.

This module provides job completion monitoring that sets an interrupt
when the OPX job finishes, allowing ConditionPollingTasks to gracefully stop.
"""

from quflow import (Workflow, Node, ParallelNode, FuncTask,
                    create_single_item_channel, ConditionPollingTask,
                    TaskContext)

from ..node_names import OPXNodeName
from ...experiment_interface import ExperimentInterface
from ...hardware import OPXContext


def check_job_is_running_and_set_interrupt(opx_ctx: OPXContext):
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
    def wrapper(ctx: TaskContext, data):
        is_running = opx_ctx.result_handles.is_processing()
        if not is_running:
            ctx.interrupt.set()

    return wrapper


def create_job_polling(
        flow: Workflow,
        interface: ExperimentInterface):
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
        task=ConditionPollingTask(func=check_job_is_running_and_set_interrupt(interface.opx_context))
    )

    flow.add_node(job_polling)

    return job_polling
