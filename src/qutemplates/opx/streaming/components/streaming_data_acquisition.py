"""Streaming data acquisition component for OPX strategies.

This module provides the streaming FETCH → POST pipeline for incremental
chunk-based data acquisition. Uses queue channels to buffer chunks.

Key differences from standard data_acquisition:
- Queue channel (buffers multiple chunks) vs single-item channel
- fetch_results() returns only new chunks vs fetch_all() accumulated data
- post_run(chunk) accumulates data vs stateless processing
"""

from quflow import Workflow, ParallelNode, FuncTask, create_queue_channel

from ...shared.node_names import OPXNodeName
from ...experiment_interface import ExperimentInterface


def create_streaming_fetch_post(flow: Workflow, interface: ExperimentInterface) -> ParallelNode:
    """
    Create streaming FETCH → POST pipeline using queue channel.

    This streaming variant uses a queue channel to buffer incremental
    chunks from fetch. Each fetch returns only new data (not accumulated).
    Post processes each chunk and aggregates in memory.

    Differences from standard:
        - Queue channel (buffers chunks) vs single-item channel
        - fetch_results() returns chunks (A, B, C) vs accumulated (A, AB, ABC)
        - post_run(chunk) accumulates vs stateless processing

    User Contract:
        - fetch_results() must return only new chunks (e.g., fetch(0))
        - post_run(chunk) must accumulate chunks and save to self.data
        - post_run(chunk) must return processed data (for live plotting)

    Args:
        flow: Workflow to add nodes to
        interface: Experiment interface with fetch_results and post_run

    Returns:
        POST node (for connecting downstream consumers like live animation)

    Example User Implementation:
        >>> class StreamingExperiment(OpxExperiment):
        ...     execution_mode = ExecutionMode.STREAMING
        ...
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.chunks = []
        ...
        ...     def fetch_results(self):
        ...         # Return only new chunks
        ...         return self.opx_context.result_handles.get('I').fetch(0)
        ...
        ...     def post_run(self, chunk):
        ...         # Accumulate chunk
        ...         if chunk is not None:
        ...             self.chunks.append(chunk)
        ...         # Process all accumulated
        ...         processed = process(self.chunks)
        ...         self.data = processed  # Save for extraction
        ...         return processed       # Return for dataflow

    Note:
        Uses ConditionPollingTask (not FuncTask) to enable polling behavior.
        Both nodes run in parallel until interrupted by job completion.
    """

    # Queue channel buffers chunks (not single-item)
    fetch_to_post = create_queue_channel()

    fetch_polling = flow.add_node(
        ParallelNode(OPXNodeName.FETCH, FuncTask(func=interface.fetch_results))
    )

    post_polling = flow.add_node(
        ParallelNode(
            OPXNodeName.POST,
            FuncTask(
                func=interface.post_run,
            ),
        )
    )

    flow.connect_dataflow(fetch_polling, post_polling, fetch_to_post)

    return post_polling
