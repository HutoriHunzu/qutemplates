from dataclasses import dataclass
from qm import QuantumMachine
from qm.jobs.running_qm_job import RunningQmJob, StreamsManager
from qm.api.v2.qm_api import QmApi


@dataclass
class OPXContext:
    qm: QuantumMachine | QmApi
    job: RunningQmJob
    result_handles: StreamsManager
    debug_script: str | None = None


