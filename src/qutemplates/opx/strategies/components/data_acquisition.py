"""Data acquisition components for OPX strategies.

This module provides the core FETCH → POST pipeline components
using ConditionPollingTask for continuous polling behavior.
"""

from quflow import (Workflow, Node, ParallelNode, FuncTask,
                    create_single_item_channel, ConditionPollingTask,
                    TaskContext)

from ...node_names import OPXNodeName
from ...experiment_interface import ExperimentInterface


def fetch_results_wrapper(func):
    """
    Adapt fetch_results() signature to ConditionPollingTask signature.

    ConditionPollingTask expects: (ctx: TaskContext, data) -> result
    But fetch_results has signature: () -> result

    This wrapper adapts the signatures by ignoring ctx and data.
    """
    def wrapper(ctx: TaskContext, data):
        return func()
    return wrapper


def post_run_wrapper(func):
    """
    Adapt post_run(data) signature to ConditionPollingTask signature.

    ConditionPollingTask expects: (ctx: TaskContext, data) -> result
    But post_run has signature: (data) -> result

    This wrapper adapts the signatures by ignoring ctx.
    """
    def wrapper(ctx: TaskContext, data):
        return func(data)
    return wrapper


def create_fetch_post_skeleton(
        flow: Workflow,
        interface: ExperimentInterface
) -> ParallelNode:
    """
    Create FETCH → POST pipeline using ConditionPollingTasks.

    Both tasks run as polling tasks that execute repeatedly until
    the job completion interrupt is triggered (by job_polling node).

    This pattern allows:
    - Continuous fetching of partial results
    - Real-time post-processing
    - Graceful shutdown when job completes

    Args:
        flow: Workflow to add nodes to
        interface: Experiment interface with fetch_results and post_run

    Returns:
        POST node (for connecting downstream consumers like live animation)

    Note:
        Uses ConditionPollingTask (not FuncTask) to enable polling behavior.
        Both nodes run in parallel until interrupted by job completion.
    """

    fetch_to_post = create_single_item_channel()

    fetch_polling = flow.add_node(ParallelNode(
        OPXNodeName.FETCH,
        ConditionPollingTask(func=fetch_results_wrapper(interface.fetch_results))
    )
    )

    post_polling = flow.add_node(ParallelNode(
        OPXNodeName.POST,
        ConditionPollingTask(
            func=post_run_wrapper(interface.post_run),
        )
    ))

    flow.connect_dataflow(fetch_polling, post_polling, fetch_to_post)

    return post_polling
