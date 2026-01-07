"""
Batch experiment strategy builders.

These builders construct workflows for BatchOPX experiments using
existing components (job polling, progress, data acquisition, live plot).

Batch pattern:
- Periodic fetch_results polling during execution (live monitoring)
- Final fetch_results + post_run after workflow completes
"""

from quflow import Workflow

from ..batch.interface import BatchInterface
from .components import (
    create_job_polling,
    create_progress_bar,
    create_fetch_post_skeleton,
    add_live_animation
)


def build_batch_standard(interface: BatchInterface) -> Workflow:
    """
    Build standard strategy for batch experiments.

    Includes:
    - Job polling (monitors completion, sets interrupt)
    - Progress bar (shows averaging progress)
    - Periodic fetch+post (live monitoring via fetch_results)
    - Live plotting (real-time updates)

    Flow:
    - FETCH (periodic) → POST → LIVE_PLOT
    - PROGRESS (monitors averager)
    - JOB_POLLING (signals completion)

    All run in parallel until job completes.
    """
    flow = Workflow()

    # Core data pipeline - periodic fetch+post for live monitoring
    post_node = create_fetch_post_skeleton(flow, interface)

    # Job monitoring - sets interrupt when done
    create_job_polling(flow, interface)

    # Progress tracking
    create_progress_bar(flow, interface)

    # Live plotting
    add_live_animation(flow, post_node, interface)

    return flow


def build_batch_minimal(interface: BatchInterface) -> Workflow:
    """
    Build minimal strategy for batch experiments.

    Includes:
    - Job polling
    - Periodic fetch+post (live monitoring)

    No progress, no live plotting.
    """
    flow = Workflow()

    # Core data pipeline
    create_fetch_post_skeleton(flow, interface)

    # Job monitoring
    create_job_polling(flow, interface)

    return flow
