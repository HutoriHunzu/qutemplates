"""
OPX execution strategies.

Defines execution strategies that determine which features are enabled
for an OPX experiment run. Each strategy specifies a different combination
of core workflow and optional features.
"""

from enum import StrEnum, auto


class OPXExecutionStrategy(StrEnum):
    """
    Execution strategies for OPX experiments.

    Each strategy determines which nodes from the task dictionary are
    actually used in the workflow and how they are connected. The strategy
    controls whether optional features like live plotting and progress
    tracking are enabled.

    All strategies include the base OPX lifecycle:
        - pre_run() (sequential, before workflow)
        - open_sequence() (sequential, connects hardware & executes QUA program)
        - Workflow graph execution (FETCH → POST and optional features)
        - close() (sequential, after workflow)

    Usage:
        >>> # Most common - use STANDARD (recommended)
        >>> experiment.execute(strategy=OPXExecutionStrategy.STANDARD)
        >>>
        >>> # Or with live animation only
        >>> experiment.execute(strategy=OPXExecutionStrategy.WITH_LIVE_ANIMATION)
        >>>
        >>> # Or minimal (just FETCH → POST)
        >>> experiment.execute(strategy=OPXExecutionStrategy.MINIMAL)
    """

    STANDARD = auto()
    MINIMAL_NO_LIVE = auto()
    MINIMAL = auto()
    WITH_PROGRESS = auto()
    WITH_LIVE_ANIMATION = auto()
    WITH_LIVE_ANIM_AND_PROGRESS = auto()
    WITH_LIVE_ACQ_AND_PROGRESS = auto()
