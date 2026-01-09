# Base infrastructure for OPX experiments
# Pure infrastructure - no execute() method, no workflow knowledge

from abc import ABC, abstractmethod
from typing import TypeVar, Any

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .hardware import Averager, OPXContext, AveragerInterface, BaseOpxHandler
from ..experiments.template import Template
from .utilities import save_all
from .constants import ExportConstants


T = TypeVar("T")


class BaseOPX(Template[T], ABC):
    """Base infrastructure for OPX experiments with hardware lifecycle and data management.

    Provides core functionality for all OPX experiment types including hardware
    connection, program execution, data registration, and export capabilities.
    Subclasses define specific execution patterns (snapshot, streaming, interactive).

    Abstract Methods:
        define_program(): Define QUA program within program context.
        construct_opx_handler(): Create OPX handler for hardware lifecycle.

    Infrastructure Provided:
        Hardware lifecycle: _open_hardware(), _close_hardware().
        Data management: reset(), register_data(), export_data(), save_all().
        Simulation: simulate() for hardware-free testing.
        Properties: opx_context, opx_handler, averager, averager_interface.

    Subclasses:
        SnapshotOPX: Fetch all accumulated data at once.
        StreamingOPX: Incremental chunk-based data fetching.
        InteractiveOPX: Point-by-point evaluation for optimization.
    """

    def __init__(self):
        self.name = ""
        self.data: T | None = None
        self.parameters: Any = None
        self._accumulated_data: dict[str, Any] = {}
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

    # Data management (Public API)

    def reset(self):
        """Reset accumulated data and context for new execution."""
        self._accumulated_data = {}
        self._opx_context = None

    def register_data(self, name: str, data: Any):
        """Register data for export with a given name."""
        self._accumulated_data[name] = data

    def export_data(self) -> dict:
        def _helper():
            for k in ExportConstants:
                v = self._accumulated_data.get(k)
                if v:
                    yield k, v

        return dict(_helper())

    def save_all(
        self,
        path: str,
        data: T,
        figs: list[Figure] | None = None,
        save_debug: bool = True,
        close_figs: bool = True,
    ):
        self.register_data(ExportConstants.DATA, data)
        export_data = self.export_data()

        if save_debug:
            debug_data = export_data.pop(ExportConstants.DEBUG, None)
        else:
            debug_data = None

        save_all(self.name, path, data=export_data, figs=figs, debug_data=debug_data)

        if close_figs and figs:
            plt.close("all")

    # Hardware lifecycle helpers

    @property
    def opx_handler(self) -> BaseOpxHandler:
        """Current OPX handler. Available after _open_hardware()."""
        if self._opx_handler is None:
            raise RuntimeError("OPX handler not available. Call _open_hardware() first.")
        return self._opx_handler

    def _open_hardware(self) -> OPXContext:
        """
        Connect to hardware and execute program.

        Updated flow:
        1. Create handler via construct_opx_handler() hook (includes config)
        2. Execute program via handler (config already in handler)
        3. Store and return context

        Returns:
            OPXContext containing job, result handles, and quantum machine

        Example - Normal execution:
            >>> exp = MyExperiment()
            >>> ctx = exp._open_hardware()  # Creates handler, executes
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
        self.opx_handler.close()

    @property
    def opx_context(self) -> OPXContext:
        """OPX execution context. Available after _open_hardware()."""
        if self._opx_context is None:
            raise RuntimeError("OPX context not available. Call _open_hardware() first.")
        return self._opx_context

    # URI: also here maybe we dont need the averager interface as property
    @property
    def averager(self) -> Averager:
        if self._averager is None:
            self._averager = Averager()
        return self._averager

    @property
    def averager_interface(self) -> AveragerInterface | None:
        return self._averager_interface

    # Simulation

    def simulate(
        self,
        duration_ns: int,
        debug_path: str | None = None,
        auto_element_thread: bool = False,
        not_strict_timing: bool = False,
        simulation_interface=None,
    ):
        """Simulate without hardware execution."""
        from .hardware.simulation import simulate_program
        from .utilities import ns_to_clock_cycles
        from qm.qua import program
        from qm import generate_qua_script

        # Create handler (this will call init_config internally via construct_opx_handler)
        handler = self.construct_opx_handler()

        # Define program
        with program() as prog:
            self.define_program()

        # Get config from handler
        config = handler.config if hasattr(handler, "config") else self.init_config()

        # Generate debug script if requested
        if debug_path:
            debug_script = generate_qua_script(prog, config)
            with open(debug_path, "w") as f:
                f.write(debug_script)

        # Setup simulation flags
        flags = []
        if auto_element_thread:
            flags.append("auto-element-thread")
        if not_strict_timing:
            flags.append("not-strict-timing")

        # Simulate
        duration_cycles = ns_to_clock_cycles(duration_ns)

        # Get QMM from handler
        qmm = handler.get_or_create_qmm() if hasattr(handler, "get_or_create_qmm") else None

        simulation_data = simulate_program(
            qmm, config, prog, duration_cycles, flags, simulation_interface
        )

        return simulation_data
