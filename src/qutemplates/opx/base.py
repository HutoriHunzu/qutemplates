# Base infrastructure for OPX experiments
# Pure infrastructure - no execute() method, no workflow knowledge

from abc import ABC, abstractmethod
from typing import TypeVar, Any

from pycircuit.components import OpxMetadata
from matplotlib.artist import Artist
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .hardware import Averager, OPXContext, OPXHandler, AveragerInterface
from ..experiments.template import Template
from .utilities import save_all
from .constants import ExportConstants


T = TypeVar('T')


class BaseOPX(Template[T], ABC):
    """Base infrastructure - shared lifecycle, no execute(). Subclasses implement their own."""

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
    def opx_metadata(self) -> OpxMetadata:
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

    # Data management

    def _reset(self):
        self._accumulated_data = {}
        self._opx_context = None

    def _register_data(self, name: str, data: Any):
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
        """Connect, execute program, return context."""
        config = self.init_config()
        self._opx_handler = OPXHandler(self.opx_metadata())
        ctx = self._opx_handler.open_and_execute(
            config,
            self.define_program,
            debug=True
        )
        self._opx_context = ctx
        return ctx

    def _close_hardware(self):
        if self._opx_handler:
            self._opx_handler.close()

    # Properties

    @property
    def opx_context(self) -> OPXContext:
        if self._opx_context is None:
            raise ValueError('Using OPX Context ')
        return self._opx_context

    @opx_context.setter
    def opx_context(self, value: OPXContext):
        self._opx_context = value

    @property
    def result_handles(self):
        return self.opx_context.result_handles

    @property
    def averager(self) -> Averager:
        if self._averager is None:
            self._averager = Averager()
        return self._averager

    @property
    def averager_interface(self) -> AveragerInterface | None:
        return self._averager_interface

    @property
    def experiment_averager(self) -> Averager:
        """Deprecated - use self.averager."""
        import warnings
        warnings.warn(
            "experiment_averager is deprecated, use averager instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.averager

    # Helpers

    def _load_averager_interface(self):
        self._averager_interface = self.averager.generate_interface(
            self.opx_context.result_handles
        )

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
