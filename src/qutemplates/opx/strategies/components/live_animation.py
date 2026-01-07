"""Live animation component for OPX strategies.

This module provides real-time plotting capability by connecting matplotlib
updates to the data pipeline.
"""

from quflow import (Workflow, Node, ParallelNode, FuncTask,
                    create_single_item_channel, ConditionPollingTask,
                    TaskContext)

from ...node_names import OPXNodeName
from ...experiment_interface import ExperimentInterface
from qutemplates.common import LiveAnimationTask


def add_live_animation(flow: Workflow,
                       data_source_node: ParallelNode,
                       interface: ExperimentInterface) -> ParallelNode:
    """
    Add live animation node to workflow.

    Creates a parallel node that receives processed data and updates a matplotlib
    plot in real-time. The node runs in the main thread (required for matplotlib)
    and receives data from the specified source node.

    Args:
        flow: Workflow to add node to
        data_source_node: Node that produces data for plotting (typically POST node)
        interface: Experiment interface with setup_plot and update_plot

    Returns:
        Created live animation node

    Example:
        >>> # In strategy:
        >>> post_node = create_fetch_post_skeleton(flow, interface)
        >>> live_node = add_live_animation(flow, post_node, interface)
        >>> # Now post_node feeds data to live_node for real-time plotting

    Note:
        Requires matplotlib and runs in main thread. The setup_plot and update_plot
        callables must be provided in the interface.
    """
    #
    if interface.averager_interface:
        get_current_average = interface.averager_interface.get_current_average
        max_avg = interface.averager_interface.total
    else:
        get_current_average = None
        max_avg = None

    # Create live animation task
    live_anim_task = LiveAnimationTask(
        setup_func=interface.setup_plot,
        update=interface.update_plot,
        refresh_time_sec=0.05,
        current_avg_callable=get_current_average,
        max_avg=max_avg
    )

    # Create parallel node (must run in main thread for matplotlib)
    live_anim_node = flow.add_node(
        ParallelNode(
            OPXNodeName.LIVE_ANIMATION,
            live_anim_task,
            run_in_main_thread=True
        )
    )

    # Wire dataflow from source to animation
    channel = create_single_item_channel()
    flow.connect_dataflow(data_source_node, live_anim_node, channel)

    return live_anim_node
