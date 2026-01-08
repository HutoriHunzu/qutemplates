"""
Base template for all experiments.

This module provides the root abstract class that all experiments inherit from,
defining the minimal interface that any experiment must implement.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class Template(ABC, Generic[T]):
    """
    Root abstract base class for all experiments.

    This is the most abstract layer - it defines only the essential public API
    that all experiments must provide, regardless of platform or implementation.

    The Template uses the Generic[T] pattern to allow type-safe specification
    of the experiment's result type.

    Example:
        >>> from dataclasses import dataclass
        >>>
        >>> @dataclass
        >>> class MyResult:
        ...     data: list[float]
        >>>
        >>> class MyExperiment(Template[MyResult]):
        ...     def execute(self):
        ...         # ... experiment logic ...
        ...         return MyResult(data=[1.0, 2.0, 3.0])
        >>>
        >>> exp = MyExperiment()
        >>> result: MyResult = exp.execute()  # Type-safe!
    """

    @abstractmethod
    def execute(self, **kwargs) -> T:
        """
        Execute the experiment and return results.

        This is the primary public API for running an experiment. All experiments
        must implement this method to define their execution logic.

        Args:
            **kwargs: Experiment-specific parameters (e.g., execution strategy,
                     debug options, etc.)

        Returns:
            Experiment result of type T

        Example:
            >>> result = experiment.execute(strategy=MyStrategy.FAST)
            >>> result = experiment.execute(debug_script_path="./debug")
        """
        pass
