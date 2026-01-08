from dataclasses import dataclass
from qm import QuantumMachine, StreamsManager
from qm.jobs.running_qm_job import RunningQmJob


from qm.api.v2.qm_api import QmApi
from qm.api.v2.job_api import JobApi


@dataclass
class OPXContext:
    qm: QuantumMachine | QmApi
    job: RunningQmJob | JobApi
    result_handles: StreamsManager
    debug_script: str | None = None
