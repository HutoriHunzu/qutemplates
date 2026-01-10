from dataclasses import dataclass

from qm import SimulatorSamples
from qm.waveform_report import WaveformReport


@dataclass
class SimulationData:
    """
    Results from QUA program simulation.

    Contains raw simulation outputs from Quantum Machines simulator.
    No processing or interpretation - just direct hardware simulation results.

    Attributes:
        samples: Simulated analog/digital samples from all elements
        waveform_report: Report of waveforms generated during simulation

    Example:
        >>> sim_data = simulate_program(qmm, config, prog, 1000)
        >>> # Inspect samples
        >>> sim_data.samples.con1.plot()
        >>> # Check waveform report
        >>> print(sim_data.waveform_report)
    """

    samples: SimulatorSamples  # SimulatedSamples from QM
    waveform_report: WaveformReport | None  # WaveformReport from QM
