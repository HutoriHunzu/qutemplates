from typing import Callable
from ...execution_mode import ExecutionMode
from .streaming_data_acquisition import create_streaming_fetch_post
from .data_acquisition import create_fetch_post_skeleton


def select_data_acquisition_component(
    execution_mode: ExecutionMode
) -> tuple[Callable, bool]:
    """
    Select data acquisition component and result flag based on execution mode.

    This helper determines which data acquisition component to use and whether
    a final fetch is needed after workflow completes.

    Args:
        execution_mode: Execution mode determining data acquisition pattern

    Returns:
        Tuple of (component_builder, needs_final_fetch) where:
        - component_builder: Function to create FETCH → POST nodes
        - needs_final_fetch: True if final fetch+post needed after workflow

    Raises:
        ValueError: If execution mode is unknown

    Example:
        >>> create_data_acq, needs_fetch = select_data_acquisition_component(
        ...     ExecutionMode.STANDARD
        ... )
        >>> post_node = create_data_acq(flow, interface)
        >>> # After workflow: if needs_fetch, call post_run(fetch_results())
    """
    if execution_mode == ExecutionMode.STANDARD:
        # Standard: fetch_all accumulated data, needs final fetch
        return create_fetch_post_skeleton, True

    elif execution_mode == ExecutionMode.STREAMING:
        # Streaming: fetch chunks, data already accumulated in memory
        return create_streaming_fetch_post, False

    else:
        raise ValueError(f"Unknown execution mode: {execution_mode}")