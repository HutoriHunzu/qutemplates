"""OPX hardware interface handler."""

from __future__ import annotations

from typing import Callable

from qm import QuantumMachinesManager, QuantumMachine, generate_qua_script
from qm.api.v2.qm_api import QmApi
from qm.qua import program

from .opx_context import OPXContext
from .base_opx_handler import BaseOpxHandler


class DefaultOpxHandler(BaseOpxHandler):
    """
    Default OPX hardware handler implementation.

    Manages standard hardware lifecycle:
    - QMM connection (shared per IP address)
    - QM lifecycle with configuration
    - QUA program execution
    - Context generation

    Configuration is passed during construction and stored as part
    of handler state. This enables:
    - Handler reuse across multiple program executions
    - Separation of config from execution
    - Custom handler subclasses with pre-configured settings

    State Management:
    - QMM: Shared per IP address via class-level dict
    - QM: Instance-level, one per handler
    - Config: Stored at construction time
    - Job: Current running job after execute()
    - Result handles: Current job's result handles

    Extensibility:
    - Subclass to customize behavior
    - Override create_qmm() for custom manager creation
    - Override open() for custom QM opening logic
    - Override close() for custom closing logic (e.g., keep-open)

    Example - Basic usage:
        >>> handler = DefaultOpxHandler(opx_metadata, config)
        >>> ctx = handler.open_and_execute(my_program, debug=True)
        >>> data = ctx.result_handles.get('I').fetch_all()
        >>> handler.close()

    Example - Custom keep-open behavior:
        >>> class KeepOpenHandler(DefaultOpxHandler):
        ...     def __init__(self, opx_metadata, config):
        ...         super().__init__(opx_metadata, config)
        ...         self.auto_close = False
        ...
        ...     def close(self):
        ...         if not self.auto_close:
        ...             return  # Skip closing
        ...         super().close()
    """

    # Class-level: Shared QMMs per IP address
    _ip_to_manager: dict[str, QuantumMachinesManager] = {}

    def __init__(self, opx_metadata, config: dict):
        """
        Initialize handler with metadata and configuration.

        Args:
            opx_metadata: OpxMetadata dataclass with connection details
                         (host_ip, port, cluster_name, etc.)
            config: QUA configuration dictionary
        """
        self.opx_metadata = opx_metadata
        self.config = config
        self._context: OPXContext | None = None

    # QMM management (shared per IP)
    @property
    def context(self) -> OPXContext:
        if self._context is None:
            raise ValueError("Accessing OPX Context without initializing it")
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
    def open(self, config: dict | None = None) -> tuple[QuantumMachinesManager, QuantumMachine | QmApi]:
        """
        Open QuantumMachine with stored or provided configuration.

        Override to customize opening behavior (e.g., config validation,
        physical/logical config splitting).

        Args:
            config: Optional config override. If None, uses self.config

        Returns:
            Tuple of (QuantumMachinesManager, QuantumMachine or QmApi)

        Raises:
            OpenQmException: If QM fails to open
        """
        config_to_use = config if config is not None else self.config
        qmm = self.get_or_create_qmm()
        qm = qmm.open_qm(config_to_use, close_other_machines=True)
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

    def open_and_execute(self, program_callable: Callable[[], None], debug: bool = False) -> OPXContext:
        """
        Execute complete lifecycle using stored configuration.

        This is the main entry point used by experiments.
        Orchestrates: open → define program → execute → return context.

        Args:
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
            >>> handler = DefaultOpxHandler(opx_metadata, config)
            >>> ctx = handler.open_and_execute(my_program, debug=True)
            >>> data = ctx.result_handles.get('I').fetch_all()
        """
        # Open QM with stored config
        qmm, qm = self.open()

        # Define QUA program
        with program() as prog:
            program_callable()

        # Generate debug script if requested
        debug_script = None
        if debug:
            debug_script = generate_qua_script(prog, self.config)

        # Execute program
        job = qm.execute(prog)

        # setting opx_context
        context = OPXContext(
            qm=qm, job=job, result_handles=job.result_handles, debug_script=debug_script
        )

        # Return fresh context
        self._context = context

        return self.context


# Backward compatibility alias
class OPXHandler(DefaultOpxHandler):
    """
    Backward compatibility alias for DefaultOpxHandler.

    DEPRECATED: Use DefaultOpxHandler directly.
    This alias maintained for existing code compatibility.

    Supports both old and new constructor signatures:
    - Old: OPXHandler(opx_metadata) - config passed to open_and_execute()
    - New: OPXHandler(opx_metadata, config) - config stored in handler

    The old signature is automatically detected and handled for compatibility.
    """

    def __init__(self, opx_metadata, config: dict | None = None):
        """
        Initialize handler with backward compatibility.

        Args:
            opx_metadata: OpxMetadata dataclass
            config: Optional QUA config. If None, uses old-style behavior
                   (config must be provided to open_and_execute())
        """
        self.opx_metadata = opx_metadata
        self._stored_config = config
        self._context: OPXContext | None = None

        # If config provided, initialize as new-style
        if config is not None:
            super().__init__(opx_metadata, config)

    def open_and_execute(
        self,
        config_or_callable: dict | Callable[[], None],
        program_callable: Callable[[], None] | None = None,
        debug: bool = False,
    ) -> OPXContext:
        """
        Execute with backward compatibility for both signatures.

        Old signature: open_and_execute(config, program_callable, debug=False)
        New signature: open_and_execute(program_callable, debug=False)

        Args:
            config_or_callable: Either config dict (old) or program callable (new)
            program_callable: Program callable (old style only)
            debug: Debug flag

        Returns:
            OPXContext with job, result handles, and QM
        """
        # Detect which signature is being used
        if program_callable is not None:
            # Old signature: (config, program_callable, debug)
            config = config_or_callable
            # Initialize parent if not already done
            if self._stored_config is None:
                # Temporarily initialize with config
                super().__init__(self.opx_metadata, config)
            return super().open_and_execute(program_callable, debug)
        else:
            # New signature: (program_callable, debug)
            if self._stored_config is None:
                raise ValueError(
                    "Config not provided during construction. "
                    "Use OPXHandler(metadata, config) or pass config to open_and_execute()"
                )
            return super().open_and_execute(config_or_callable, debug)
