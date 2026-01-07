"""
OPX workflow node names.

Defines standard node names for OPX experiment workflows. These names are used
as node identifiers in the workflow graph and as keys in task dictionaries.

Note: PRE, OPEN_SEQUENCE, and CLOSE are NOT included here because they are
sequential operations that run outside the workflow graph, not as nodes.
"""

from enum import StrEnum, auto


class OPXNodeName(StrEnum):
    """
    Standard node names for OPX workflow graphs.

    These names identify nodes in the workflow graph. Each node represents
    either a core data acquisition step or an optional feature that runs
    in parallel with the main workflow.

    Core Data Acquisition Nodes:
        FETCH: Fetch results from OPX hardware
        POST: Post-process fetched data

    Feature Nodes (Optional, run in parallel):
        LIVE_ANIMATION: Real-time matplotlib plotting
        PROGRESS: Progress bar display
        JOB_STATUS_POLLING: Non-blocking job completion monitoring
        LIVE_DATA_FETCH: Continuous data fetching during execution
        LIVE_DATA_POST: Process live data before plotting

    Interactive Workflow Nodes:
        INTERACTIVE: Generator-based data streaming
        AGGREGATE: Aggregate streamed data

    Usage:
        >>> tasks = {
        ...     OPXNodeName.FETCH: FuncTask(experiment.fetch_results),
        ...     OPXNodeName.POST: FuncTask(experiment.post_run),
        ...     OPXNodeName.LIVE_ANIMATION: LiveAnimationTask(...)
        ... }
        >>> workflow = build_opx_workflow(tasks, strategy)

    Note:
        PRE, OPEN_SEQUENCE, and CLOSE are sequential operations that run
        directly (not as workflow nodes), so they are not included in this enum.
        - PRE: Pre-run setup (called before workflow)
        - OPEN_SEQUENCE: Connect hardware, execute QUA program (called before workflow)
        - CLOSE: Disconnect hardware (called after workflow)
    """

    # Core data acquisition nodes
    FETCH = auto()
    """Fetch results from OPX hardware (blocking until ready)"""

    POST = auto()
    """Post-process fetched data"""

    # Optional feature nodes (run in parallel)
    LIVE_ANIMATION = auto()
    """Real-time matplotlib animation/plotting (runs in main thread)"""

    PROGRESS = auto()
    """Progress bar display using tqdm"""

    JOB_STATUS_POLLING = auto()
    """Non-blocking job completion monitoring (replaces blocking wait)"""

    LIVE_DATA_FETCH = auto()
    """Continuous data fetching during job execution"""

    LIVE_DATA_POST = auto()
    """Process live data before sending to animation"""

    # Interactive workflow nodes
    INTERACTIVE = auto()
    """Generator-based data streaming (for interactive experiments)"""

    AGGREGATE = auto()
    """Aggregate streamed data (for interactive experiments)"""
