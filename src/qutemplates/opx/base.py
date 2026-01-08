# Base infrastructure for OPX experiments
# Pure infrastructure - no execute() method, no workflow knowledge

from abc import ABC, abstractmethod
from typing import TypeVar, Any

from matplotlib.artist import Artist
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .hardware import Averager, OPXContext, OPXHandler, AveragerInterface
from ..experiments.template import Template
from .utilities import save_all
from .constants import ExportConstants


T = TypeVar('T')


class BaseOPX(Template[T], ABC):
    """
    Base infrastructure for OPX experiments - provides hardware lifecycle and data management.

    This class provides:
    - Hardware lifecycle: _open_hardware(), _close_hardware()
    - Data management: reset(), register_data(), export_data(), save_all()
    - Abstract hardware setup: opx_metadata(), init_config(), define_program()

    Subclasses (BatchOPX, StreamingOPX, InteractiveOPX) add their own execution patterns.
    """

    def __init__(self):
        self.name = ''
        self.data: T | None = None
        self.parameters: Any = None
        self._accumulated_data: dict[str, Any] = {}
        self._opx_context: OPXContext | None = None
        self._opx_handler: OPXHandler | None = None
        self._averager: Averager | None = None
        self._averager_interface: AveragerInterface | None = None

    # Abstract methods - hardware setup

    @abstractmethod
    def opx_metadata(self) -> 'OpxMetadata':
        """Hardware connection metadata."""
        pass

    @abstractmethod
    def init_config(self) -> dict:
        """QUA config dictionary."""
        pass

    @abstractmethod
    def define_program(self):
        """QUA program definition (called within program context)."""
        pass

    # Hardware management hooks

    def create_opx_handler(self) -> OPXHandler:
        """
        Create OPX hardware handler.

        Override this method to customize handler creation or provide
        a pre-opened handler from elsewhere.

        Returns:
            OPXHandler instance

        Example - Custom handler creation:
            >>> class MyExperiment(BatchOPX):
            ...     def __init__(self, shared_handler=None):
            ...         super().__init__()
            ...         self._shared = shared_handler
            ...
            ...     def create_opx_handler(self):
            ...         if self._shared:
            ...             return self._shared
            ...         return super().create_opx_handler()
        """
        return OPXHandler(self.opx_metadata())

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
        close_figs: bool = True
    ):
        self.register_data(ExportConstants.DATA, data)
        export_data = self.export_data()

        if save_debug:
            debug_data = export_data.pop(ExportConstants.DEBUG, None)
        else:
            debug_data = None

        save_all(self.name, path, data=export_data, figs=figs, debug_data=debug_data)

        if close_figs and figs:
            plt.close('all')

    # Hardware lifecycle helpers
    def _open_hardware(self) -> OPXContext:
        """
        Connect to hardware and execute program.

        Pure orchestration method that calls hooks for each step:
        1. Check if context already exists (from previous execution)
        2. Create handler if needed (via create_opx_handler hook)
        3. Check if handler has active context and reuse it
        4. Execute normal flow (config + program) if no active context

        Smart hardware reuse:
        - If handler was set via set_opx_handler() with active context,
          reuses that context without reopening hardware
        - If handler is fresh or context closed, executes normally
        - Enables maintaining hardware state between experiments

        Returns:
            OPXContext containing job, result handles, and quantum machine

        Example - Normal execution:
            >>> exp = MyExperiment()
            >>> ctx = exp._open_hardware()  # Creates handler, executes

        Example - Hardware reuse:
            >>> exp1 = MyExperiment()
            >>> exp1.execute()  # Opens hardware
            >>>
            >>> exp2 = MyExperiment()
            >>> exp2.set_opx_handler(exp1._opx_handler)  # Share handler
            >>> ctx = exp2._open_hardware()  # Reuses active context!
        """
        # Step 1: Already have context? Return it
        if self._opx_context is not None:
            return self._opx_context

        # Step 2: Create handler if needed (hook - can be overridden)
        if self._opx_handler is None:
            self._opx_handler = self.create_opx_handler()

        # Step 3: Handler has active context? Reuse it
        if self._opx_handler.has_active_context:
            self._opx_context = self._opx_handler.active_context
            return self._opx_context

        # Step 4: Fresh handler - normal flow (calls abstract methods)
        config = self.init_config()  # Abstract method: get config
        ctx = self._opx_handler.open_and_execute(
            config,
            self.define_program,  # Abstract method: define program
            debug=True
        )

        # Store and return
        self._opx_context = ctx
        return ctx

    def _close_hardware(self):
        if self._opx_handler:
            self._opx_handler.close()

    # Properties

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
        simulation_interface=None
    ):
        """Simulate without hardware execution."""
        from .hardware.simulation import simulate_program
        from .utilities import ns_to_clock_cycles
        from qm.qua import program
        from qm import generate_qua_script

        self.pre_run()
        config = self.init_config()

        opx_handler = OPXHandler(self.opx_metadata())

        with program() as prog:
            self.define_program()

        if debug_path:
            debug_script = generate_qua_script(prog, config)
            with open(debug_path, 'w') as f:
                f.write(debug_script)

        flags = []
        if auto_element_thread:
            flags.append('auto-element-thread')
        if not_strict_timing:
            flags.append('not-strict-timing')

        duration_cycles = ns_to_clock_cycles(duration_ns)
        simulation_data = simulate_program(
            opx_handler.qmm,
            config,
            prog,
            duration_cycles,
            flags,
            simulation_interface
        )

        return simulation_data
