"""OPX hardware interface handler."""

import logging
from typing import Callable

from qm import QuantumMachinesManager, QuantumMachine, Program, generate_qua_script
from qm.jobs.running_qm_job import RunningQmJob, StreamsManager
from qm.api.v2.qm_api import QmApi
from qm.exceptions import QmFailedToCloseQuantumMachineError, OpenQmException
from qm.octave import QmOctaveConfig, ClockMode
from qm.qua import program

from pycircuit.components import OpxMetadata
from .opx_context import OPXContext

logger = logging.getLogger(__name__)


class OPXHandler:
    """
    Singleton OPX handler that works with a provided OpxMetadata dataclass.

    Implements singleton pattern keyed by IP address - only one handler
    instance exists per physical OPX machine. This prevents multiple
    experiments from conflicting and enables hardware reuse via keep_open flag.

    If octave_ip is present in OpxMetadata, it sets up the QmOctaveConfig automatically.
    """

    _ip_to_manager: dict[str, QuantumMachinesManager] = {}
    _instances: dict[str, 'OPXHandler'] = {}  # Singleton instances keyed by IP

    def __new__(cls, opx_metadata: OpxMetadata):
        """
        Return singleton instance for this metadata's IP address.

        Args:
            opx_metadata: OpxMetadata with host_ip identifying the machine

        Returns:
            Singleton OPXHandler instance for this IP address
        """
        key = opx_metadata.host_ip  # Key by IP address

        if key not in cls._instances:
            # Create new singleton instance for this IP
            instance = super().__new__(cls)
            cls._instances[key] = instance
            instance._initialized = False  # Flag for __init__
        return cls._instances[key]

    def __init__(self, opx_metadata: OpxMetadata):
        """
        Initialize OPX handler (only once per singleton).

        Args:
            opx_metadata: An OpxMetadata dataclass instance with
                         host_ip, port, cluster_name, octave_ip, etc.

        Note:
            Only initializes on first call for this IP address.
            Subsequent calls with same IP return existing instance unchanged.
        """
        # Only initialize once per singleton instance
        if self._initialized:
            return

        self.opx_metadata = opx_metadata
        self.qm: QuantumMachine | QmApi | None = None
        self.job: RunningQmJob | None = None
        self.result_handles: StreamsManager | None = None
        self._active_context: OPXContext | None = None
        self.keep_open: bool = False  # Flag to prevent close()
        self._initialized = True


    def _create_new_manager(self) -> QuantumMachinesManager:
        octave_config = None
        if self.opx_metadata.octave_ip:
            octave_config = QmOctaveConfig()
            octave_config.add_device_info(
                'oct1',
                self.opx_metadata.octave_ip,
                self.opx_metadata.octave_port
            )
            octave_config.set_calibration_db(self.opx_metadata.octave_calibration_path)

        return QuantumMachinesManager(
            host=self.opx_metadata.host_ip,
            port=self.opx_metadata.port,
            cluster_name=self.opx_metadata.cluster_name,
            octave_calibration_db_path=(
                None if self.opx_metadata.octave_ip
                else self.opx_metadata.octave_calibration_path
            ),
            octave=octave_config
        )

    @property
    def qmm(self):
        ip = self.opx_metadata.host_ip
        manager = self._ip_to_manager.get(ip)
        if manager is None:
            manager = self._create_new_manager()
            self._ip_to_manager[ip] = manager
        return manager

    @property
    def has_active_context(self) -> bool:
        """
        Check if handler has an active running context.

        Returns True if this handler has successfully executed a program
        and maintains an active context with running job and quantum machine.

        Returns:
            True if active context exists with valid qm and job, False otherwise

        Example:
            >>> handler = OPXHandler(metadata)
            >>> handler.has_active_context  # False
            >>> ctx = handler.open_and_execute(config, program, debug=True)
            >>> handler.has_active_context  # True
            >>> handler.close()
            >>> handler.has_active_context  # False
        """
        return (self._active_context is not None and
                self.qm is not None and
                self.job is not None)

    @property
    def active_context(self) -> OPXContext | None:
        """
        Get active context if available.

        Returns the stored OPXContext from the most recent open_and_execute()
        call, or None if no context exists or hardware has been closed.

        Returns:
            OPXContext instance if active, None otherwise

        Example:
            >>> handler = OPXHandler(metadata)
            >>> ctx = handler.open_and_execute(config, program, debug=True)
            >>> reused_ctx = handler.active_context  # Same as ctx
        """
        return self._active_context


    def open(self, config: dict) -> QuantumMachine | QmApi:
        """
        Opens a QuantumMachine using the given config.
        Closes other machines on the same ports if needed.
        Also sets Octave clock mode if specified.
        """
        try:
            self.qm = self.qmm.open_qm(config, close_other_machines=True)
        except OpenQmException as open_qm_exception:
            logger.error(f"Failed to open QM with config={config}")
            raise open_qm_exception

        # If the user has an octave IP and clock mode, set it
        if self.opx_metadata.octave_ip and self.opx_metadata.octave_clock_mode:
            self.qm.octave.set_clock(
                "oct1",
                clock_mode=getattr(ClockMode, self.opx_metadata.octave_clock_mode)
            )
        return self.qm

    def execute(self, prog: Program) -> RunningQmJob:
        """
        Executes the given QUA program on the current QuantumMachine,
        storing the job internally.

        Uses active_context as the single source of truth for quantum machine state.
        """
        # Check for active context with quantum machine
        if self._active_context is None or self._active_context.qm is None:
            raise RuntimeError("No open QuantumMachine. Call open(config) first.")

        # Execute program using active context's QM
        self.job = self._active_context.qm.execute(prog)
        self.result_handles = self.job.result_handles

        # Update active context with new job and handles
        self._active_context = OPXContext(
            qm=self._active_context.qm,
            job=self.job,
            result_handles=self.result_handles,
            debug_script=self._active_context.debug_script
        )

        # Keep backward compat attributes in sync
        self.qm = self._active_context.qm

        return self.job

    def wait_for_all_results(self) -> None:
        """
        Waits for all results from the current job.

        Uses active_context as the single source of truth for result handles.
        """
        if self._active_context is None or self._active_context.result_handles is None:
            raise RuntimeError("No active context with result handles.")
        self._active_context.result_handles.wait_for_all_results()

    def close(self) -> None:
        """
        Closes the currently open QuantumMachine, if any,
        and logs whether it was successful.

        Uses active_context as the single source of truth for quantum machine state.

        If keep_open flag is True, skips actual closing but logs the request.
        This allows keeping hardware open between experiments while maintaining
        the close() call interface.
        """
        # Check if keep_open flag prevents closing
        if self.keep_open:
            if self._active_context and self._active_context.qm:
                logger.debug(
                    f"keep_open=True, skipping close for QM {self._active_context.qm.id}. "
                    "Hardware remains open for reuse."
                )
            return

        # Check if there's an active context to close
        if self._active_context is None or self._active_context.qm is None:
            return

        try:
            open_machines = self.qmm.list_open_qms()
            qm_id = self._active_context.qm.id

            if qm_id in open_machines:
                self._active_context.qm.close()
                logger.debug(f"Quantum Machine {qm_id} closed successfully.")
            else:
                logger.warning(
                    f"Machine ID {qm_id} not found in list_open_qms()."
                )
        except QmFailedToCloseQuantumMachineError as err:
            logger.error(f"FAILED to close Quantum Machine {qm_id}.\n{err}")
            raise err
        finally:
            # Clear active context and backward compat attributes
            self._active_context = None
            self.qm = None
            self.job = None
            self.result_handles = None


    def open_and_execute(
        self,
        config: dict,
        program_callable: Callable[[], None],
        debug: bool
    ) -> OPXContext:
        """
        Open quantum machine, execute QUA program, and return execution context.

        This is the main hardware entry point for OPX experiments. It orchestrates
        the complete lifecycle from connection to program execution:

        1. Opens quantum machine with provided config
        2. Creates QUA program context and calls user's program definition
        3. Optionally generates debug script for inspection
        4. Executes program on hardware
        5. Returns OPXContext with all session state

        The returned OPXContext contains everything needed to interact with
        the running job: result handles for data fetching, job reference for
        status monitoring, quantum machine reference, and optional debug script.

        Args:
            config: QUA configuration dictionary defining hardware setup
                   (elements, pulses, waveforms, etc.)
            program_callable: User-defined function containing QUA program logic.
                            Called within `with program() as prog:` context.
                            Should have signature: () -> None
            debug: If True, generates QUA script for debugging/inspection

        Returns:
            OPXContext containing:
                - qm: QuantumMachine or QmApi instance (session-scoped)
                - job: RunningQmJob for status monitoring
                - result_handles: StreamsManager for data fetching
                - debug_script: Optional QUA script string (if debug=True)

        Raises:
            RuntimeError: If quantum machine fails to open or execute
            OpenQmException: If QM connection fails

        Example:
            >>> handler = OPXHandler(opx_metadata)
            >>> config = {'version': 1, 'controllers': {...}, ...}
            >>>
            >>> def my_program():
            ...     # QUA statements here
            ...     measure('readout', 'resonator', None, ...)
            >>>
            >>> ctx = handler.open_and_execute(config, my_program, debug=True)
            >>> # Now fetch results using ctx.result_handles
            >>> I = ctx.result_handles.get('I').fetch_all()

        Note:
            This method stores qm, job, and result_handles on self for
            backward compatibility with methods like close(). However,
            the returned OPXContext should be the primary interface for
            accessing these objects in workflows.
        """
        # Open quantum machine with config
        self.open(config)

        # Define QUA program
        with program() as prog:
            program_callable()

        # Generate debug script if requested
        if debug:
            debug_script = generate_qua_script(prog, config)
        else:
            debug_script = None

        # Execute program on hardware
        self.execute(prog)

        # Create and store context with session-specific state
        ctx = OPXContext(
            result_handles=self.result_handles,
            job=self.job,
            qm=self.qm,
            debug_script=debug_script
        )
        self._active_context = ctx

        return ctx



