# Interactive experiment: point-by-point evaluation

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from ..base import BaseOPX
from ..handler import BaseOpxHandler, OPXContext

# Two type parameters: Point (input) and Result (output)
Point = TypeVar("Point")
Result = TypeVar("Result")


class InteractiveOPX(BaseOPX, Generic[Point, Result]):
    """Interactive template: point-by-point evaluation for optimizers.

    For external optimizers that evaluate parameter points iteratively.
    Implement define_program(), construct_opx_handler(), send_point(),
    fetch_measurement(), and process_measurement().

    Usage patterns:
    1. Context manager: with exp.open() as evaluate: result = evaluate(point)
    2. Manual: exp.setup() → exp.evaluate(point) → exp.cleanup()
    3. Batch: results = exp.run(points)
    """

    def __init__(self) -> None:
        super().__init__()
        self._opx_handler_active = False
        self._opx_context: OPXContext | None = None
        self.data: list[Result] = []

    @property
    def opx_context(self) -> OPXContext:
        """Current execution context. Available after setup()."""
        if self._opx_context is None:
            raise ValueError("Context not available. Call setup() first.")
        return self._opx_context

    # Abstract - user must implement

    @abstractmethod
    def send_point(self, point: Point):
        """Send parameter point to running program."""
        pass

    @abstractmethod
    def fetch_measurement(self):
        """Fetch single measurement (blocks until available)."""
        pass

    @abstractmethod
    def process_measurement(self, measurement) -> Result:
        """Process single measurement into result."""
        pass

    # Optional - user can override

    def pre_run(self):
        """Setup before execution."""
        pass

    # Context manager support

    def open(self):
        """
        Open hardware and return context manager for evaluation.

        Usage:
            with exp.open() as evaluate:
                result = evaluate(point)

        The context manager automatically handles setup and cleanup,
        and returns the evaluate function for use.

        Returns:
            Self (for context manager protocol)
        """
        return self

    def __enter__(self):
        """
        Enter context: setup hardware and return evaluate function.

        Returns:
            Bound evaluate method that can be called with points
        """
        self.setup()
        return self.evaluate

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context: cleanup hardware.

        Ensures cleanup happens even if an exception occurs during evaluation.

        Returns:
            False (does not suppress exceptions)
        """
        self.cleanup()
        return False

    # Interactive execution methods

    def setup(self):
        """Start program, prepare for interactive evaluation."""
        self.pre_run()
        self._opx_context = self.opx_handler.open_and_execute()
        self._opx_handler_active = True

    def evaluate(self, point: Point) -> Result:
        """
        Evaluate single point and return result.

        Args:
            point: Parameter point to evaluate

        Returns:
            Processed result for the given point

        Raises:
            RuntimeError: If hardware is not active (call setup() first or use open() context manager)
        """
        if not self._opx_handler_active:
            raise RuntimeError("Hardware not active. Call setup() or use open() context manager.")
        self.send_point(point)
        measurement = self.fetch_measurement()
        result = self.process_measurement(measurement)
        return result

    def run(self, points: Iterable[Point]) -> list[Result]:
        """
        Convenience: evaluate multiple points sequentially.

        Automatically handles setup and cleanup. Ensures cleanup happens
        even if an exception occurs during evaluation.

        Args:
            points: Iterable of points to evaluate

        Returns:
            List of results for each point
        """
        self.setup()
        results = []
        try:
            for point in points:
                result = self.evaluate(point)
                results.append(result)
        finally:
            self.cleanup()

        self.data = results
        return results

    def cleanup(self):
        """Stop program and close hardware."""
        if self._opx_handler_active:
            self.opx_handler.close()
            self._opx_handler_active = False
            self._opx_context = None
