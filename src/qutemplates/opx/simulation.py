"""QUA program simulation."""

from dataclasses import dataclass

from qm import CompilerOptionArguments, FullQuaConfig, QuantumMachinesManager, SimulationConfig
from qm import SimulatorSamples
from qm.waveform_report import WaveformReport


@dataclass
class SimulationData:
    """Results from QUA program simulation.

    Attributes:
        samples: Simulated analog/digital samples from all elements
        waveform_report: Report of waveforms generated during simulation
    """

    samples: SimulatorSamples
    waveform_report: WaveformReport | None


def simulate_program(
    qmm: QuantumMachinesManager,
    config: FullQuaConfig,
    program,
    duration_cycles: int,
    flags: list[str] | None = None,
    simulation_interface=None,
) -> SimulationData:
    """Simulate QUA program without hardware execution.

    Args:
        qmm: QuantumMachinesManager instance
        config: QUA configuration dictionary
        program: QUA program object to simulate
        duration_cycles: Simulation duration in clock cycles (4ns per cycle)
        flags: Optional compiler flags (e.g., 'auto-element-thread')
        simulation_interface: Optional simulation interface

    Returns:
        SimulationData containing samples and waveform report
    """
    job = qmm.simulate(
        config=config,
        program=program,
        simulate=SimulationConfig(
            duration=duration_cycles,
            include_analog_waveforms=True,
            simulation_interface=simulation_interface,
        ),
        compiler_options=CompilerOptionArguments(flags=flags or []),
    )

    return SimulationData(
        samples=job.get_simulated_samples(),
        waveform_report=job.get_simulated_waveform_report(),
    )
