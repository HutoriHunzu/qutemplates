# OPX Architecture

This document describes the architecture of OPX experiment templates.

## Overview

The package provides a layered architecture for running OPX experiments:

```
BaseOPX (contract)
    |
    v
SnapshotOPX (template)  <-->  DefaultOpxHandler (handler)
```

## Templates

Templates define execution patterns for experiments. Each template inherits from `BaseOPX` and implements its own `execute()` and `simulate()` methods with specific semantics.

### SnapshotOPX

For experiments where data accumulates continuously and is fetched at the end.

```python
class MyExperiment(SnapshotOPX):
    def define_program(self):
        # QUA program definition
        pass

    def construct_opx_handler(self):
        return DefaultOpxHandler(self.metadata, self.config, self.define_program)

    def fetch_results(self):
        return self.opx_handler.context.result_handles.get("I").fetch_all()
```

Run with: `experiment.execute(strategy="live_plotting_with_progress")`

Strategies: `wait_for_all`, `wait_for_progress`, `live_plotting`, `live_plotting_with_progress`

## Handler

Handlers manage the hardware lifecycle: open, execute/simulate, close.

### DefaultOpxHandler

Standard implementation with:
- Shared QMM per IP address (avoids reconnection overhead)
- Program building from callable
- Full execution and simulation support

Override `create_qmm()` for custom manager creation (e.g., with Octave).

### Convenience Methods

```python
handler.open_and_execute()  # Opens, executes, stores context
handler.open_and_simulate(duration_ns)  # Opens, simulates, closes
handler.close()  # Closes stored connection
```

## BaseOPX Contract

Minimal abstract base that templates must implement:

- `define_program()` - QUA program definition
- `construct_opx_handler()` - Create handler instance

Provides:
- `opx_handler` property (lazy initialization)

Templates own their execution semantics - BaseOPX has no `execute()` or `simulate()` methods.
