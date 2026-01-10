"""OPX context and connection dataclasses."""

from dataclasses import dataclass

from qm import QuantumMachine, QuantumMachinesManager, StreamsManager
from qm.api.v2.job_api import JobApi
from qm.api.v2.qm_api import QmApi
from qm.jobs.running_qm_job import RunningQmJob


@dataclass
class OPXManagerAndMachine:
    """Manager and machine pair returned by handler.open()."""

    manager: QuantumMachinesManager
    machine: QuantumMachine | QmApi


@dataclass
class OPXContext:
    """Execution context with job and result handles."""

    manager: QuantumMachinesManager
    qm: QuantumMachine | QmApi
    job: RunningQmJob | JobApi
    result_handles: StreamsManager
