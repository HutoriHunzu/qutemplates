"""Strategy components for building OPX workflows.

This package contains reusable building blocks that strategies compose
to create complete workflow graphs. Each component handles a specific
aspect of OPX experiment execution.

Components:
- data_acquisition: Core FETCH → POST pipeline (STANDARD mode)
- streaming_data_acquisition: Streaming FETCH → POST pipeline (STREAMING mode)
- job_polling: Job completion monitoring and interrupt signaling
- progress: Progress bar display using Averager
- live_animation: Real-time matplotlib plotting
"""

from .data_acquisition import create_fetch_post_skeleton
from .streaming_data_acquisition import create_streaming_fetch_post
from .job_polling import create_job_polling
from .progress import create_progress_bar
from .live_animation import add_live_animation
from .selector import select_data_acquisition_component

__all__ = [
    'create_fetch_post_skeleton',
    'create_streaming_fetch_post',
    'create_job_polling',
    'create_progress_bar',
    'add_live_animation',
    'select_data_acquisition_component'
]
