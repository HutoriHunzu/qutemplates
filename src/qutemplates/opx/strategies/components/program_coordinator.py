"""Program coordinator component for streaming experiments.

This component handles the program_coordinator pattern where:
- User controls the fetch loop inside program_coordinator()
- Framework calls program_coordinator ONCE
- User writes chunks to output queue
- Post_run processes chunks as they arrive
"""

from quflow import (Workflow, ParallelNode, FuncTask, create_queue_channel)

from ...node_names import OPXNodeName
from ...streaming.interface import StreamingInterface


def create_program_coordinator_pipeline(
    flow: Workflow,
    interface: StreamingInterface
) -> ParallelNode:
    """
    Create program coordinator pipeline for streaming experiments.

    Pattern:
    - Framework calls program_coordinator() ONCE (not polled)
    - User implements fetch loop inside, writes to queue
    - Post_run node consumes from queue and processes chunks

    Args:
        flow: Workflow to add nodes to
        interface: Streaming interface with program_coordinator and post_run

    Returns:
        POST node (for connecting live animation)

    User Contract:
        - program_coordinator(job, handles, queue) implements the fetch loop
        - User writes chunks to queue as they're fetched
        - post_run(chunk) processes each chunk, returns for live plotting
    """
    # Queue for coordinator → post communication
    coordinator_to_post = create_queue_channel()

    # Coordinator node - called ONCE, user controls loop
    coordinator_node = flow.add_node(ParallelNode(
        OPXNodeName.FETCH,  # Reuse FETCH name for consistency
        FuncTask(func=lambda: _run_coordinator(interface, coordinator_to_post))
    ))

    # Post node - processes chunks from queue
    post_node = flow.add_node(ParallelNode(
        OPXNodeName.POST,
        FuncTask(func=interface.post_run)
    ))

    # Connect pipeline
    flow.connect_dataflow(coordinator_node, post_node, coordinator_to_post)

    return post_node


def _run_coordinator(interface: StreamingInterface, output_queue):
    """
    Run program coordinator with proper arguments.

    Extracts job and result_handles from interface context and passes
    to user's program_coordinator along with the output queue.
    """
    job = interface.opx_context.job
    result_handles = interface.opx_context.result_handles

    # Call user's coordinator - they control the loop
    interface.program_coordinator(job, result_handles, output_queue)
