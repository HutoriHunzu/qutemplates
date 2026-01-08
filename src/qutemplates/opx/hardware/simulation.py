"""QUA program simulation utilities.

This module provides hardware-level simulation functionality that operates
independently of the experiment workflow system. It wraps QM's simulation
API for direct use.
"""

from dataclasses import dataclass
from typing import Any

from qm import SimulationConfig, CompilerOptionArguments


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
    samples: Any  # SimulatedSamples from QM
    waveform_report: Any  # WaveformReport from QM


def simulate_program(
    qmm,
    config: dict,
    program,
    duration_cycles: int,
    flags: list[str] | None = None,
    simulation_interface = None
) -> SimulationData:
    """
    Simulate QUA program without hardware execution.

    Pure hardware-level operation with no experiment coupling. Directly
    calls qmm.simulate() and returns raw simulation results.

    This function bypasses all experiment infrastructure (workflow, strategies,
    data acquisition, etc.) and provides direct access to QM's simulation API.

    Args:
        qmm: QuantumMachinesManager instance
        config: QUA configuration dictionary defining hardware setup
        program: QUA program object to simulate
        duration_cycles: Simulation duration in clock cycles (4ns per cycle)
        flags: Optional compiler flags for simulation:
               - 'auto-element-thread': Enable automatic element threading
               - 'not-strict-timing': Relax strict timing constraints
        simulation_interface: Optional simulation interface for custom behavior

    Returns:
        SimulationData containing samples and waveform report

    Raises:
        Any exceptions from qmm.simulate() (connection errors, program errors, etc.)

    Example:
        >>> from qm import QuantumMachinesManager
        >>> from qm.qua import program, play
        >>>
        >>> qmm = QuantumMachinesManager(host='localhost')
        >>> config = {...}  # QUA config
        >>>
        >>> with program() as prog:
        ...     play('pulse', 'element')
        >>>
        >>> sim_data = simulate_program(
        ...     qmm, config, prog,
        ...     duration_cycles=1000,
        ...     flags=['auto-element-thread']
        ... )
        >>>
        >>> # Inspect results
        >>> sim_data.samples.con1.plot()

    Note:
        Duration must be in clock cycles (1 cycle = 4ns).
        Use utilities.ns_to_clock_cycles() to convert from nanoseconds.
    """
    # Execute simulation
    job = qmm.simulate(
        config=config,
        program=program,
        simulate=SimulationConfig(
            duration=duration_cycles,
            include_analog_waveforms=True,
            simulation_interface=simulation_interface
        ),
        compiler_options=CompilerOptionArguments(flags=flags or [])
    )

    # Extract results
    return SimulationData(
        samples=job.get_simulated_samples(),
        # samples=None,
        waveform_report=job.get_simulated_waveform_report()
    )
