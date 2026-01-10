# qutemplates

Templates for OPX experiments built on [quflow](https://github.com/...).

## Quick Start

```python
from qutemplates.opx.snapshot import SnapshotOPX
from qutemplates.opx.handler import DefaultOpxHandler

class MyExperiment(SnapshotOPX):
    def define_program(self):
        # QUA program
        pass

    def construct_opx_handler(self):
        return DefaultOpxHandler(self.metadata, self.config, self.define_program)

    def fetch_results(self):
        return self.opx_handler.context.result_handles.get("I").fetch_all()

# Run
exp = MyExperiment()
data = exp.execute()
```

## Templates

- **SnapshotOPX** - Fetch all accumulated data at once. Supports live plotting and progress tracking.

## Documentation

- [OPX Architecture](docs/opx-architecture.md) - Templates, handlers, and base contract

## Installation

```bash
pip install .
```
