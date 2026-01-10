# Base infrastructure for OPX experiments
# Pure infrastructure - no execute() method, no workflow knowledge

from abc import ABC, abstractmethod

from .handler import Averager, AveragerInterface, BaseOpxHandler, OPXContext


class BaseOPX(ABC):
    """Minimal OPX hardware lifecycle contract.

    Provides core infrastructure for OPX experiment templates:
    - Abstract methods for program definition and handler construction
    - Hardware lifecycle: _open_hardware(), _close_hardware()
    - Handler and context management via properties
    - Averager support for progress tracking
    - Simulation capabilities

    Templates must implement:
        define_program(): Define QUA program within program context.
        construct_opx_handler(): Create OPX handler for hardware lifecycle.

    Templates own their execution semantics:
        SnapshotOPX: Fetch all accumulated data at once.
        StreamingOPX: Incremental chunk-based data fetching.
        InteractiveOPX: Point-by-point evaluation for optimization.
    """

    def __init__(self):
        self._opx_context: OPXContext | None = None
        self._opx_handler: BaseOpxHandler | None = None
        self._averager: Averager | None = None
        self._averager_interface: AveragerInterface | None = None

    @abstractmethod
    def define_program(self):
        """QUA program definition (called within program context)."""
        pass

    @abstractmethod
    def construct_opx_handler(self) -> BaseOpxHandler:
        """Construct OPX handler for hardware lifecycle management.

        Creates and configures the handler that manages hardware connection,
        program execution, and cleanup. Called once during _open_hardware().

        Returns:
            BaseOpxHandler: Configured handler instance.

        Note:
            Default implementation: DefaultOpxHandler(self.opx_metadata(), self.init_config())
            Custom handlers: Override for specialized behavior (e.g., KeepAliveHandler).
        """
        pass

    @property
    def opx_handler(self) -> BaseOpxHandler:
        if self._opx_handler is None:
            self._opx_handler = self.construct_opx_handler()
        return self._opx_handler

    # Hardware lifecycle helpers

    def _open_hardware(self) -> OPXContext:
        """Connect to hardware and execute program.

        Returns:
            OPXContext containing job, result handles, and quantum machine.
        """
        # Create handler with config via abstract method
        handler = self.construct_opx_handler()

        # Execute program (config already in handler)
        ctx = handler.open_and_execute(
            self.define_program,  # Abstract method: define program
            debug=True,
        )

        # Store and return
        self._opx_handler = handler
        self._opx_context = ctx
        return ctx

    def _close_hardware(self):
        """Close hardware connection via handler."""
        self.opx_handler.close()

    @property
    def opx_context(self) -> OPXContext:
        """OPX execution context. Available after _open_hardware()."""
        if self._opx_context is None:
            raise RuntimeError("OPX context not available. Call _open_hardware() first.")
        return self._opx_context

    @property
    def averager(self) -> Averager:
        if self._averager is None:
            self._averager = Averager()
        return self._averager

    @property
    def averager_interface(self) -> AveragerInterface | None:
        return self._averager_interface

    # Simulation

    def _build_program(self):
        """Build QUA program by calling define_program() within program context."""
        from qm.qua import program
        with program() as prog:
            self.define_program()
        return prog

    def simulate(
        self,
        duration_ns: int,
        debug_path: str | None = None,
        auto_element_thread: bool = False,
        not_strict_timing: bool = False,
        simulation_interface=None,
    ):
        """Simulate program without hardware execution.

        Args:
            duration_ns: Simulation duration in nanoseconds.
            debug_path: Optional path to save QUA debug script.
            auto_element_thread: Enable auto-element-thread simulation flag.
            not_strict_timing: Enable not-strict-timing simulation flag.
            simulation_interface: Optional simulation interface.

        Returns:
            Simulation data from QM simulator.
        """
        from qm import generate_qua_script

        from .handler.simulation import simulate_program
        from .utilities import ns_to_clock_cycles

        # Create handler with config
        handler = self.construct_opx_handler()

        # Build program
        prog = self._build_program()

        # Generate debug script if requested
        if debug_path:
            debug_script = generate_qua_script(prog, handler.config)
            with open(debug_path, "w") as f:
                f.write(debug_script)

        # Setup simulation flags
        flags = []
        if auto_element_thread:
            flags.append("auto-element-thread")
        if not_strict_timing:
            flags.append("not-strict-timing")

        # Simulate using handler's QMM and config
        duration_cycles = ns_to_clock_cycles(duration_ns)
        qmm = handler.get_or_create_qmm() if hasattr(handler, "get_or_create_qmm") else None

        return simulate_program(
            qmm, handler.config, prog, duration_cycles,
            flags, simulation_interface
        )
