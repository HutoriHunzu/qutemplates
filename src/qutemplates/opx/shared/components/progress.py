"""Progress bar component for OPX strategies.

This module provides progress tracking for experiments using the Averager interface.
"""

from quflow import Workflow, ParallelNode

from qutemplates.opx.hardware.averager import AveragerInterface

from ..node_names import OPXNodeName
from qutemplates.common.tasks import ProgressTask


def create_progress_bar(flow: Workflow, averager_interface: AveragerInterface):
    """
    Add progress bar node to workflow.

    Creates a parallel node that continuously fetches the current averaging
    count from the OPX and displays a progress bar using tqdm.

    Requires that the experiment uses the Averager pattern and provides
    an averager_interface in the ExperimentInterface.

    Args:
        flow: Workflow to add node to
        interface: Experiment interface with averager_interface

    Returns:
        Created progress node

    Note:
        The progress bar updates by calling averager_interface.update() which
        fetches the current count from the OPX result_handles stream.
        Runs until interrupted by job completion.
    """

    progress_node = ParallelNode(
        name=OPXNodeName.PROGRESS,
        task=ProgressTask(get_current=averager_interface.update, total=averager_interface.total),
    )

    flow.add_node(progress_node)

    return progress_node
