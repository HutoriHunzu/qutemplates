"""Data acquisition components for OPX strategies.

This module provides the core FETCH → POST pipeline components
using ConditionPollingTask for continuous polling behavior.
"""

from quflow import (
    OutputFuncTask,
    ParallelNode,
    PollingTask,
    TransformFuncTask,
    Workflow,
    create_single_item_channel,
)

from ..shared.node_names import OPXNodeName
from .interface import SnapshotInterface


def create_fetch_post_skeleton(flow: Workflow, interface: SnapshotInterface) -> ParallelNode:
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

    fetch_polling = flow.add_node(
        ParallelNode(
            OPXNodeName.FETCH,
            PollingTask(task=OutputFuncTask(func=interface.fetch_results)),
        )
    )

    post_polling = flow.add_node(
        ParallelNode(
            OPXNodeName.POST,
            PollingTask(
                task=TransformFuncTask(func=interface.post_run),
            ),
        )
    )

    flow.connect_dataflow(fetch_polling, post_polling, fetch_to_post)

    return post_polling
