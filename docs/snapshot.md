# SnapshotOPX

Template for experiments where data accumulates continuously and is fetched at the end of execution.

## Overview

SnapshotOPX provides a complete workflow for OPX experiments with:
- Automatic hardware lifecycle management
- Optional live plotting during execution
- Optional progress tracking with tqdm
- Artifact collection for saving results
- Simulation support

Subclass `SnapshotOPX` and implement the required methods to create your experiment.

---

## Required Methods

You must implement these three methods:

### define_program()

Return a QUA `program` object defining your experiment logic.

```python
def define_program(self):
    with program() as prog:
        n = declare(int)
        I = declare(fixed)
        I_stream = declare_stream()

        with for_(n, 0, n < 100, n + 1):
            measure("readout", "resonator", None, dual_demod.full("cos", "sin", I))
            save(I, I_stream)

        with stream_processing():
            I_stream.buffer(100).average().save("I")

    return prog
```

### construct_opx_handler()

Return a handler instance that manages the OPX connection.

```python
def construct_opx_handler(self):
    return DefaultOpxHandler(self.metadata, self.config)
```

> [!NOTE]
> `self.metadata` should contain `host_ip`, `port`, and `cluster_name`.
> `self.config` is your QUA configuration dictionary.

### fetch_results()

Fetch and return data from the hardware after execution completes.

```python
def fetch_results(self):
    handles = self.context.result_handles
    handles.wait_for_all_values()
    return {
        "I": handles.get("I").fetch_all(),
        "Q": handles.get("Q").fetch_all(),
    }
```

> [!IMPORTANT]
> `self.context` is only available after `execute()` starts.
> The returned data is passed to `post_run()` for processing.

---

## Optional Methods

### pre_run()

Called before execution starts. Use for setup that depends on runtime state.

```python
def pre_run(self):
    self.parameters = {"n_avg": self.n_avg, "frequency": self.freq}
    print(f"Starting experiment with {self.n_avg} averages")
```

### post_run(data)

Process raw data from `fetch_results()`. Return value becomes `exp.data`.

```python
def post_run(self, data) -> ProcessedData:
    return ProcessedData(
        I=np.mean(data["I"], axis=0),
        Q=np.mean(data["Q"], axis=0),
        amplitude=np.abs(data["I"] + 1j * data["Q"]),
    )
```

### setup_plot() and update_plot()

Required for live plotting. See [Live Plotting](#live-plotting) section.

---

## Execution

### Basic Execution

```python
exp = MyExperiment()
data = exp.execute()
```

### Execution with Strategy

```python
data = exp.execute(strategy="live_plotting_with_progress")
```

### Execution Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `strategy` | `str` | Workflow strategy (see below) |
| `show_execution_graph` | `bool` | Display quflow workflow graph before running |
| `debug_script_path` | `Path` | Save QUA script to file with timestamp |

### Strategies

| Strategy | Progress Bar | Live Plot | Description |
|----------|:------------:|:---------:|-------------|
| `wait_for_all` | - | - | Minimal - polls job completion only |
| `wait_for_progress` | Yes | - | Progress bar without visualization |
| `live_plotting` | - | Yes | Live plot without progress bar |
| `live_plotting_with_progress` | Yes | Yes | All features (default) |

> [!NOTE]
> Progress tracking requires using `self.averager` in your QUA program.
> Live plotting requires implementing `setup_plot()` and `update_plot()`.

---

## Instance Attributes

After creating an instance, you can set these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Experiment name (used in saved files) |
| `parameters` | `Any` | Parameters to save with artifacts |
| `status` | `Status` | Current status: `PENDING`, `RUNNING`, `FINISHED` |

After execution:

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `T` | Result from `post_run()` |
| `context` | `OPXContext` | Hardware context with result handles |
| `artifacts` | `ArtifactRegistry` | Collected artifacts for saving |

---

## Progress Tracking with Averager

The `Averager` class enables progress tracking by streaming the loop counter from the OPX.

### Setup

Set the total count and use `self.averager` in your QUA program:

```python
class MyExperiment(SnapshotOPX):
    def __init__(self):
        super().__init__()
        self.n_avg = 1000

    def define_program(self):
        with program() as prog:
            # Initialize averager variables (creates counter and stream)
            n = self.averager.init_vars()
            self.averager.total = self.n_avg

            I = declare(fixed)
            I_stream = declare_stream()

            with for_(n, 0, n < self.n_avg, n + 1):
                measure("readout", "resonator", None, dual_demod.full("cos", "sin", I))
                save(I, I_stream)

                # Save current count to stream (required for progress)
                self.averager.update_count()

            with stream_processing():
                I_stream.buffer(self.n_avg).average().save("I")
                # Add averager stream processing
                self.averager.stream_processing()

        return prog
```

### Averager Methods

| Method | When to Call | Description |
|--------|--------------|-------------|
| `init_vars()` | Before loop | Creates counter variable and stream, returns counter |
| `update_count()` | Inside loop | Saves current count to stream |
| `stream_processing()` | In stream_processing block | Saves stream with configured name |

> [!IMPORTANT]
> All three methods must be called in the correct order:
> 1. `init_vars()` - before the averaging loop
> 2. `update_count()` - inside the loop (each iteration)
> 3. `stream_processing()` - in the stream_processing block

### Averager Properties

| Property | Type | Description |
|----------|------|-------------|
| `total` | `int` | Total iterations (set before program) |
| `save_name` | `str` | Stream name (default: `"repetition_number"`) |
| `n` | `QuaVariable` | The counter variable (after `init_vars()`) |
| `count` | `QuaVariable` | Alias for `n` |

---

## Live Plotting

Enable real-time visualization during execution by implementing `setup_plot()` and `update_plot()`.

### setup_plot()

Create the figure and return matplotlib artists that will be updated.

```python
def setup_plot(self) -> tuple[Figure, list[Artist]]:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Create artists with empty data
    line_I, = ax1.plot([], [], 'b-', label='I')
    line_Q, = ax2.plot([], [], 'r-', label='Q')

    # Configure axes
    ax1.set_xlabel("Frequency (MHz)")
    ax1.set_ylabel("I (a.u.)")
    ax1.set_xlim(self.freq_min, self.freq_max)
    ax1.set_ylim(-1, 1)

    ax2.set_xlabel("Frequency (MHz)")
    ax2.set_ylabel("Q (a.u.)")
    ax2.set_xlim(self.freq_min, self.freq_max)
    ax2.set_ylim(-1, 1)

    return fig, [line_I, line_Q]
```

### update_plot()

Update artists with new data. Called periodically during execution.

```python
def update_plot(self, artists: list[Artist], data) -> list[Artist]:
    line_I, line_Q = artists

    line_I.set_data(self.frequencies, data.I)
    line_Q.set_data(self.frequencies, data.Q)

    # Autoscale if needed
    line_I.axes.relim()
    line_I.axes.autoscale_view()

    return artists
```

> [!TIP]
> Modify artists in-place rather than creating new ones for better performance.
> The same artist list is passed to each `update_plot()` call.

### One-Shot Plotting

For static plots after execution, use the `plot()` method:

```python
data = exp.execute()
fig = exp.plot(data)
plt.show()
```

This calls `setup_plot()` then `update_plot()` once.

---

## Simulation

Test your QUA program without hardware:

```python
sim_data = exp.simulate(duration_ns=10000)
```

### Simulation Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `duration_ns` | `int` | Simulation duration in nanoseconds |
| `debug_path` | `str` | Save QUA script to file |
| `auto_element_thread` | `bool` | Enable auto-element-thread flag |
| `not_strict_timing` | `bool` | Enable not-strict-timing flag |
| `simulation_interface` | `SimulationInterface` | Custom QM simulation interface |

### SimulationData

The returned `SimulationData` contains:
- `analog`: Dict of analog waveforms per element/port
- `digital`: Dict of digital waveforms per element/port

```python
sim_data = exp.simulate(duration_ns=10000)
plt.plot(sim_data.analog["resonator"]["output1"])
```

---

## Artifact Export

SnapshotOPX automatically collects artifacts during execution:
- Parameters (set via `self.parameters`)
- Data (from `post_run()`)
- QUA script (generated automatically)

### Saving Artifacts

```python
exp.save_all(
    save_dir=Path("./results"),
    data=data,
    fig=fig  # Optional figure to include
)
```

Files created:
- `{name}_parameters.json`
- `{name}_data.npz` (or `.json` depending on type)
- `{name}_script.py`
- `{name}_figure.png` (if fig provided)

### Custom Artifacts

Register additional artifacts before calling `save_all()`:

```python
exp.artifacts.register("custom_data", my_array, kind=ArtifactKind.NPZ)
```
