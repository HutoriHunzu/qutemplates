"""
Experiment interface for dependency injection.

This module provides the interface dataclass that packages experiment methods
and callables for passing to the graph builder. This enables clean dependency
injection without coupling to the experiment object.
"""

from dataclasses import dataclass
from typing import Callable, Any, Generator
from .hardware import OPXContext, AveragerInterface


@dataclass
class ExperimentInterface:
    """
    Package of experiment methods and callables for dependency injection.

    This interface decouples the experiment object from workflow builders
    (strategies). Instead of passing the entire experiment object ('self'),
    we pass individual functions and state needed for workflow construction.

    This enables:
    - Clean dependency injection without tight coupling
    - Strategy builders can use only what they need
    - Clear contract of what experiment provides to workflows
    - Testability (can inject mock callables)

    Different strategies use different subsets of the interface:
    - MINIMAL: fetch_results, post_run, opx_context
    - STANDARD: All fields (fetch, post, plotting, progress, job polling)
    - WITH_LIVE_ANIMATION: fetch, post, setup_plot, update_plot, opx_context

    Lifecycle:
        1. OpxExperiment.execute() creates this interface after opening hardware
        2. Interface passed to solve_strategy() → builder function
        3. Builder function constructs workflow using interface callables
        4. Workflow executes, calling interface methods as needed

    Attributes:
        fetch_results: Callable that fetches data from hardware result handles.
                      Signature: () -> Any
        post_run: Callable that post-processes fetched data.
                 Signature: (data: Any) -> Any
        opx_context: OPXContext containing qm, job, result_handles, debug_script.
                    Used by features to access hardware session state.
        setup_plot: Optional callable to setup matplotlib plot for live animation.
                   Signature: () -> (figure, artists)
        update_plot: Optional callable to update plot with new data.
                    Signature: (artists, data) -> artists
        averager_interface: Optional AveragerInterface for progress tracking.
                          Used by progress bar and live plotting features.
        experiment_name: Optional name of experiment for display in logs/UI

    Example:
        >>> # Created by experiment (users don't typically create this manually):
        >>> interface = ExperimentInterface(
        ...     fetch_results=exp.fetch_results,
        ...     post_run=exp.post_run,
        ...     opx_context=exp.opx_context,
        ...     setup_plot=exp.setup_plot,
        ...     update_plot=exp.update_plot,
        ...     averager_interface=exp.averager.generate_interface(result_handles),
        ...     experiment_name=exp.name
        ... )
        >>>
        >>> # Used by strategy builder:
        >>> def build_minimal(interface: ExperimentInterface) -> Workflow:
        ...     flow = Workflow()
        ...     # Use interface.fetch_results to create tasks
        ...     return flow
    """

    # Core data pipeline
    fetch_results: Callable[[], Any]
    post_run: Callable[[Any], Any]

    # Hardware session state
    opx_context: OPXContext

    # Optional - for live plotting feature
    setup_plot: Callable | None = None
    update_plot: Callable | None = None

    # Optional - for progress tracking feature
    averager_interface: AveragerInterface | None = None

    # Metadata
    experiment_name: str | None = None
