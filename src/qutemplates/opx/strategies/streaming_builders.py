"""
Streaming experiment strategy builders.

These builders construct workflows for StreamingOPX experiments using
existing components plus new program_coordinator component.

Streaming pattern:
- program_coordinator called ONCE (user controls fetch loop)
- User writes chunks to queue
- post_run processes chunks continuously
- get_aggregated_data() + final post_run() after workflow
"""

from quflow import Workflow

from ..streaming.interface import StreamingInterface
from .components import (
    create_job_polling,
    create_progress_bar,
    add_live_animation
)
from .components.program_coordinator import create_program_coordinator_pipeline


def build_streaming_standard(interface: StreamingInterface) -> Workflow:
    """
    Build standard strategy for streaming experiments.

    Includes:
    - Job polling (monitors completion, sets interrupt)
    - Progress bar (shows averaging progress)
    - Program coordinator (user controls fetch loop, writes to queue)
    - Live plotting (real-time updates from post_run)

    Flow:
    - COORDINATOR (called once) → POST (processes chunks) → LIVE_PLOT
    - PROGRESS (monitors averager)
    - JOB_POLLING (signals completion)

    User controls fetch loop inside program_coordinator.
    """
    flow = Workflow()

    # Core pipeline - coordinator writes, post processes
    post_node = create_program_coordinator_pipeline(flow, interface)

    # Job monitoring
    create_job_polling(flow, interface)

    # Progress tracking
    create_progress_bar(flow, interface)

    # Live plotting
    add_live_animation(flow, post_node, interface)

    return flow


def build_streaming_minimal(interface: StreamingInterface) -> Workflow:
    """
    Build minimal strategy for streaming experiments.

    Includes:
    - Job polling
    - Program coordinator pipeline

    No progress, no live plotting.
    """
    flow = Workflow()

    # Core pipeline
    create_program_coordinator_pipeline(flow, interface)

    # Job monitoring
    create_job_polling(flow, interface)

    return flow
