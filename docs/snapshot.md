# SnapshotOPX

Template for experiments where data accumulates and is fetched at end.

## Required Methods

| Method | Description |
|--------|-------------|
| `define_program()` | QUA program definition |
| `construct_opx_handler()` | Return handler instance |
| `fetch_results()` | Fetch data from hardware |

## Optional Methods

| Method | Description |
|--------|-------------|
| `pre_run()` | Setup before execution |
| `post_run(data)` | Process fetched data |
| `setup_plot()` | Return `(Figure, list[Artist])` for live plotting |
| `update_plot(artists, data)` | Update artists with new data |

## Execution Strategies

```python
exp.execute(strategy="live_plotting_with_progress")  # default
```

| Strategy | Description |
|----------|-------------|
| `wait_for_all` | Poll job completion only |
| `wait_for_progress` | Add progress bar (requires Averager) |
| `live_plotting` | Add live animation |
| `live_plotting_with_progress` | All features |

## Progress Tracking

Use `self.averager` in `define_program()`:

```python
def define_program(self):
    with program() as prog:
        self.averager.init_vars()
        with for_(n, 0, n < N, n + 1):
            # ... measurement ...
            self.averager.update_count()
        self.averager.stream_processing()
    return prog
```
