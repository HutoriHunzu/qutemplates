# Interactive experiment: point-by-point evaluation

from abc import abstractmethod
from typing import TypeVar, Generic, Iterable

from ..base import BaseOPX
from ..hardware import BaseOpxHandler, DefaultOpxHandler


# Two type parameters: Point (input) and Result (output)
Point = TypeVar("Point")
Result = TypeVar("Result")


class InteractiveOPX(BaseOPX[list[Result]], Generic[Point, Result]):
    """
    Interactive OPX experiment for point-by-point evaluation (optimizer-driven).

    This template is designed for external optimizers that need to evaluate
    individual parameter points and use the results to decide the next point.

    Three usage patterns supported:

    1. **Context Manager (Recommended)**:
        with exp.open() as evaluate:
            for point in optimizer_points:
                result = evaluate(point)

    2. **Manual Control**:
        exp.setup()
        try:
            for point in optimizer_points:
                result = exp.evaluate(point)
        finally:
            exp.cleanup()

    3. **Batch Convenience**:
        results = exp.run(points)

    Type Parameters:
        Point: Input parameter type
        Result: Output result type
    """

    def __init__(self):
        super().__init__()
        self._opx_handler_active = False

    def construct_opx_handler(self) -> BaseOpxHandler:
        """
        Create default OPX handler for interactive experiments.

        Override to provide custom handler:
            class MyInteractiveExperiment(InteractiveOPX):
                def construct_opx_handler(self):
                    return CustomHandler(self.opx_metadata(), self.init_config())

        Returns:
            DefaultOpxHandler configured for this experiment
        """
        return DefaultOpxHandler(self.opx_metadata(), self.init_config())

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
        self.reset()
        self.pre_run()

        # Open hardware
        self._open_hardware()
        self._load_averager_interface()
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
            self._close_hardware()
            self._opx_handler_active = False

    # No execute() method - use setup() → evaluate() → cleanup() pattern
