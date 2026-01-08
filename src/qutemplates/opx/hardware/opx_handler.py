"""OPX hardware interface handler."""
from __future__ import annotations

from typing import Callable

from qm import QuantumMachinesManager, QuantumMachine, generate_qua_script
from qm.api.v2.qm_api import QmApi
from qm.qua import program

from .opx_context import OPXContext


class OPXHandler:
    """
    OPX hardware handler - governs QMM and QM lifecycle.

    Responsibilities:
    - Manage QuantumMachinesManager (one per IP address, shared)
    - Open/close QuantumMachine (one per configuration)
    - Execute QUA programs
    - Generate OPXContext on demand

    State Management:
    - QMM: Shared per IP address via class-level dict
    - QM: Instance-level, one per handler
    - Job: Current running job after execute()
    - Result handles: Current job's result handles

    Extensibility:
    - Subclass to customize behavior
    - Override create_qmm() for custom manager creation
    - Override open() for custom QM opening logic
    - Override close() for custom closing logic (e.g., keep-open)
    - Override execute() for custom execution logic

    Example - Basic usage:
        >>> handler = OPXHandler(opx_metadata)
        >>> ctx = handler.open_and_execute(config, my_program, debug=True)
        >>> data = ctx.result_handles.get('I').fetch_all()
        >>> handler.close()

    Example - Custom keep-open behavior:
        >>> class KeepOpenHandler(OPXHandler):
        ...     def __init__(self, opx_metadata):
        ...         super().__init__(opx_metadata)
        ...         self.auto_close = False
        ...
        ...     def close(self):
        ...         if not self.auto_close:
        ...             return  # Skip closing
        ...         super().close()
    """

    # Class-level: Shared QMMs per IP address
    _ip_to_manager: dict[str, QuantumMachinesManager] = {}

    def __init__(self, opx_metadata):
        """
        Initialize OPX handler.

        Args:
            opx_metadata: OpxMetadata dataclass with connection details
                         (host_ip, port, cluster_name, etc.)
        """
        self.opx_metadata = opx_metadata
        self._context: OPXContext | None = None
        # self.qm: QuantumMachine | None = None
        # self.job: RunningQmJob | None = None
        # self.result_handles: StreamsManager | None = None

    # QMM management (shared per IP)
    @property
    def context(self) -> OPXContext:
        if self._context is None:
            raise ValueError('Accessing OPX Context without initializing it')
        return self._context


    def get_or_create_qmm(self) -> QuantumMachinesManager:
        """
        Get or create QuantumMachinesManager for this IP address.

        QMM is shared across all handlers connecting to the same IP.
        Override to customize manager lookup/creation logic.

        Returns:
            QuantumMachinesManager instance for this IP
        """
        ip = self.opx_metadata.host_ip
        if ip not in self._ip_to_manager:
            self._ip_to_manager[ip] = self.create_qmm()
        return self._ip_to_manager[ip]

    def create_qmm(self) -> QuantumMachinesManager:
        """
        Create new QuantumMachinesManager.

        Override to customize manager creation (e.g., add octave config).

        Returns:
            New QuantumMachinesManager instance

        Example - Add octave:
            >>> def create_qmm(self):
            ...     octave_config = QmOctaveConfig()
            ...     octave_config.add_device_info('oct1', ip, port)
            ...     return QuantumMachinesManager(
            ...         host=self.opx_metadata.host_ip,
            ...         port=self.opx_metadata.port,
            ...         cluster_name=self.opx_metadata.cluster_name,
            ...         octave=octave_config
            ...     )
        """
        return QuantumMachinesManager(
            host=self.opx_metadata.host_ip,
            port=self.opx_metadata.port,
            cluster_name=self.opx_metadata.cluster_name,
        )

    # QM lifecycle
    def open(self, config: dict) -> tuple[QuantumMachinesManager, QuantumMachine | QmApi]:
        """
        Open QuantumMachine with given configuration.

        Override to customize opening behavior (e.g., config validation,
        physical/logical config splitting).

        Args:
            config: QUA configuration dictionary

        Returns:
            Opened QuantumMachine instance

        Raises:
            OpenQmException: If QM fails to open
        """
        qmm = self.get_or_create_qmm()
        qm = qmm.open_qm(config, close_other_machines=True)
        return qmm, qm

    def close(self) -> None:
        """
        Close the current QuantumMachine.

        Override to customize closing behavior (e.g., keep-open logic).

        Raises:
            QmFailedToCloseQuantumMachineError: If QM fails to close

        Example - Keep-open override:
            >>> def close(self):
            ...     if self.keep_open_flag:
            ...         logger.debug("Keeping QM open")
            ...         return
            ...     super().close()
        """

        qm = self.context.qm
        qm.close()

    # Context generation (no caching)

    def open_and_execute(
        self,
        config: dict,
        program_callable: Callable[[], None],
        debug: bool = False
    ) -> OPXContext:
        """
        High-level: Open QM, execute program, return context.

        This is the main entry point used by experiments.
        Orchestrates the complete lifecycle: open → define program → execute → return context.

        Args:
            config: QUA configuration dictionary
            program_callable: Function containing QUA program logic.
                            Called within `with program() as prog:` context.
                            Signature: () -> None
            debug: If True, generates debug script

        Returns:
            OPXContext with job, result handles, QM, and optional debug script

        Example:
            >>> def my_program():
            ...     measure('readout', 'qubit', None, ...)
            >>>
            >>> ctx = handler.open_and_execute(config, my_program, debug=True)
            >>> data = ctx.result_handles.get('I').fetch_all()
        """
        # Open QM with config
        qmm, qm = self.open(config)

        # Define QUA program
        with program() as prog:
            program_callable()

        # Generate debug script if requested
        debug_script = None
        if debug:
            debug_script = generate_qua_script(prog, config)

        # Execute program
        job = qm.execute(prog)

        # setting opx_context
        context = OPXContext(
            qm=qm,
            job=job,
            result_handles=job.result_handles,
            debug_script=debug_script)

        # Return fresh context
        self._context = context
        
        return self.context
