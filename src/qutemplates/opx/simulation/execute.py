from qm import CompilerOptionArguments, FullQuaConfig, QuantumMachinesManager, SimulationConfig

from .structure import SimulationData


def simulate_program(
    qmm: QuantumMachinesManager,
    config: FullQuaConfig,
    program,
    duration_cycles: int,
    flags: list[str] | None = None,
    simulation_interface=None,
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
            simulation_interface=simulation_interface,
        ),
        compiler_options=CompilerOptionArguments(flags=flags or []),
    )

    # Extract results
    return SimulationData(
        samples=job.get_simulated_samples(),
        waveform_report=job.get_simulated_waveform_report(),
    )
