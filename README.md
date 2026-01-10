# qutemplates

Experiment templates for Quantum Machines OPX hardware, built on [quflow](https://github.com/HutoriHunzu/quflow.git).

## Installation

```bash
pip install .
```

## Quick Start

```python
from qutemplates.opx.snapshot import SnapshotOPX
from qutemplates.opx.handler import DefaultOpxHandler

class MyExperiment(SnapshotOPX):
    def define_program(self):
        # QUA program definition
        pass

    def construct_opx_handler(self):
        return DefaultOpxHandler(self.metadata, self.config, self.define_program)

    def fetch_results(self):
        return self.context.result_handles.get("I").fetch_all()

exp = MyExperiment()
data = exp.execute()
```

See [Architecture Guide](docs/opx-architecture.md) for details on templates and handlers.

## Development

```bash
uv sync              # Install dependencies
ruff check src/      # Lint
ruff format src/     # Format
```
