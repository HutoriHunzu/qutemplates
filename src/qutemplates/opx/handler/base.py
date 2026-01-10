"""Abstract handler for OPX hardware lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod

from qm import FullQuaConfig

from ..context import OPXManagerAndMachine


class BaseOpxHandler(ABC):
    """Abstract base class for OPX hardware handlers.

    Handlers manage hardware lifecycle only: open() and close().
    Execution and simulation logic lives in BaseOPX.
    """

    @abstractmethod
    def __init__(self, opx_metadata, config: FullQuaConfig):
        """Initialize handler with metadata and config.

        Args:
            opx_metadata: Connection details (host, port, cluster name).
            config: QUA configuration dictionary.
        """
        pass

    @abstractmethod
    def open(self) -> OPXManagerAndMachine:
        """Open connection to quantum hardware.

        Returns:
            OPXManagerAndMachine: Tuple-like object with manager and machine.

        Raises:
            OpenQmException: If hardware connection fails.
        """
        pass

    @abstractmethod
    def close(self, manager_and_machine: OPXManagerAndMachine | None = None) -> None:
        """Close connection to quantum hardware.

        Args:
            manager_and_machine: Connection to close. If None, uses stored connection.

        Raises:
            QmFailedToCloseQuantumMachineError: If close fails.
        """
        pass
