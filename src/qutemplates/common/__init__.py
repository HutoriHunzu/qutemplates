"""
Generic task templates for workflow orchestration.

This module provides platform-agnostic task implementations that can be used
with any workflow execution system. Tasks follow the dependency injection pattern,
receiving all configuration via constructor parameters rather than relying on
context or global state.

Available Tasks:
    - LiveAnimationTask: Real-time matplotlib animation with data updates
    - ProgressTask: tqdm-based progress bar with polling
"""

from .live_animation_task import LiveAnimationTask
from .progress_task import ProgressTask

__all__ = [
    "LiveAnimationTask",
    "ProgressTask",
]
