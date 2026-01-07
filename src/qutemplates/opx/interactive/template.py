# Interactive experiment: point-by-point evaluation

from abc import abstractmethod
from typing import TypeVar, Generic, Iterable

from ..base_opx import BaseOPX


# Two type parameters: Point (input) and Result (output)
Point = TypeVar('Point')
Result = TypeVar('Result')


class InteractiveOPX(BaseOPX[list[Result]], Generic[Point, Result]):
    """Interactive: point-by-point evaluation, optimizer-driven."""

    def __init__(self):
        super().__init__()
        self._opx_handler_active = False

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
        """Evaluate single point and return result."""
        self.send_point(point)
        measurement = self.fetch_measurement()
        result = self.process_measurement(measurement)
        return result

    def run(self, points: Iterable[Point]) -> list[Result]:
        """Convenience: evaluate multiple points sequentially."""
        self.setup()

        results = []
        for point in points:
            result = self.evaluate(point)
            results.append(result)

        self.data = results
        self.cleanup()
        return results

    def cleanup(self):
        """Stop program and close hardware."""
        if self._opx_handler_active:
            self._close_hardware()
            self._opx_handler_active = False

    # No execute() method - use setup() → evaluate() → cleanup() pattern
