"""
Generic wiring helpers for connecting tasks in workflows.

Provides simple, platform-agnostic utilities for wiring common task patterns
into workflow graphs. These helpers have no opinions about workflow structure
or naming conventions - they simply perform the requested wiring operations.

All node names are provided as parameters to maintain platform independence.
"""

from quflow import Workflow, Node, ParallelNode, create_single_item_channel

from .tasks.live_animation_task import LiveAnimationTask
from .tasks.progress_task import ProgressTask


def add_live_animation(
    workflow: Workflow,
    data_source_node: Node,
    live_animation_task: LiveAnimationTask,
    node_name: str
) -> Node:
    """
    Wire a live animation task to receive data from a source node.

    This is a generic helper that works with any workflow structure. It:
    1. Creates a parallel node with the live animation task
    2. Connects dataflow from data source to live animation via single-item channel
    3. Ensures the task runs in the main thread (required for matplotlib)

    Args:
        workflow: Workflow to modify
        data_source_node: Node that produces data for the animation
        live_animation_task: Pre-configured LiveAnimationTask instance
        node_name: Name for the created live animation node

    Returns:
        The created live animation node

    Example:
        >>> from qutemplates.common.tasks import LiveAnimationTask
        >>> from qutemplates.common.wiring_helpers import add_live_animation
        >>>
        >>> task = LiveAnimationTask(setup_func=..., update=...)
        >>> fetch_node = workflow.get_node_by_name('FETCH')
        >>> anim_node = add_live_animation(
        ...     workflow, fetch_node, task, 'LIVE_ANIMATION'
        ... )

    Note:
        The live animation task MUST run in the main thread to avoid
        concurrency issues with matplotlib. This is enforced by
        ParallelNode(..., run_in_main_thread=True).
    """
    # Create parallel node that runs in main thread
    live_anim_node = workflow.add_node(
        ParallelNode(
            node_name,
            live_animation_task,
            run_in_main_thread=True  # Required for matplotlib
        )
    )

    # Connect dataflow: data_source → live_animation
    channel = create_single_item_channel()
    workflow.connect_dataflow(data_source_node, live_anim_node, channel)

    return live_anim_node


def add_progress_tracking(
    workflow: Workflow,
    progress_task: ProgressTask,
    node_name: str,
    depends_on: Node | list[Node] | None = None
) -> Node:
    """
    Add a progress tracking task to the workflow.

    This is a generic helper that works with any workflow structure. It:
    1. Creates a parallel node with the progress task
    2. Optionally connects dependencies to control execution order

    Args:
        workflow: Workflow to modify
        progress_task: Pre-configured ProgressTask instance
        node_name: Name for the created progress node
        depends_on: Optional node(s) that must complete before progress starts.
                   Can be a single Node or a list of Nodes.

    Returns:
        The created progress node

    Example:
        >>> from qutemplates.common.tasks import ProgressTask
        >>> from qutemplates.common.wiring_helpers import add_progress_tracking
        >>>
        >>> task = ProgressTask(
        ...     get_current=lambda: exp.current,
        ...     get_total=lambda: exp.total,
        ...     title="Processing"
        ... )
        >>> polling_node = workflow.get_node_by_name('JOB_STATUS_POLLING')
        >>> progress_node = add_progress_tracking(
        ...     workflow, task, 'PROGRESS', depends_on=polling_node
        ... )

    Note:
        Progress task runs as a parallel node, polling callbacks until
        its stop_callable returns True. It does not block the main workflow.
    """
    # Create parallel progress node
    progress_node = workflow.add_node(
        ParallelNode(node_name, progress_task)
    )

    # Add dependencies if specified
    if depends_on is not None:
        # Handle single node or list of nodes
        nodes = depends_on if isinstance(depends_on, list) else [depends_on]
        for node in nodes:
            workflow.connect_dependency(node, progress_node)

    return progress_node


def connect_data_pipeline(
    workflow: Workflow,
    source_node: Node,
    target_node: Node
) -> None:
    """
    Connect two nodes with a single-item data channel.

    This is a simple helper for the common pattern of connecting a data
    source to a data consumer with a single-item channel (most recent value).

    Args:
        workflow: Workflow to modify
        source_node: Node that produces data
        target_node: Node that consumes data

    Example:
        >>> fetch_node = workflow.get_node_by_name('FETCH')
        >>> post_node = workflow.get_node_by_name('POST')
        >>> connect_data_pipeline(workflow, fetch_node, post_node)

    Note:
        Uses create_single_item_channel() which only stores the most
        recent value. For queue-based channels, use quflow's
        create_queue_channel() directly.
    """
    channel = create_single_item_channel()
    workflow.connect(source_node, target_node, channel)
