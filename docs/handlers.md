# Handlers

Handlers manage the OPX hardware lifecycle: opening connections, executing programs, and closing cleanly. They abstract away connection management so experiments can focus on the QUA program logic.

---

## DefaultOpxHandler

The standard handler that caches `QuantumMachinesManager` instances per IP address.

### Basic Usage

```python
def construct_opx_handler(self):
    return DefaultOpxHandler(self.metadata, self.config)
```

Where:
- `self.metadata` has `host_ip`, `port`, `cluster_name` attributes
- `self.config` is your QUA configuration dictionary

### How It Works

```
First experiment on IP 192.168.1.100:
  1. Creates new QuantumMachinesManager for 192.168.1.100
  2. Caches manager in class-level dict
  3. Opens QuantumMachine with your config

Second experiment on same IP:
  1. Retrieves cached manager (no reconnection!)
  2. Opens new QuantumMachine with your config

Different IP (192.168.1.101):
  1. Creates new QuantumMachinesManager for this IP
  2. Caches separately
```

> [!NOTE]
> The QMM cache is at the class level, shared across all `DefaultOpxHandler` instances.
> This avoids reconnection overhead when running multiple experiments.

### Handler Lifecycle

The handler manages this lifecycle automatically:

```python
handler.open()      # Get/create QMM, open QM with config
handler.execute()   # Execute program, return OPXContext
handler.close()     # Close the QuantumMachine
```

> [!IMPORTANT]
> You don't call these directly - `SnapshotOPX.execute()` manages the lifecycle.
> The handler is constructed lazily via `construct_opx_handler()`.

### Customization

Override `create_qmm()` to customize the manager (e.g., for Octave):

```python
class OctaveHandler(DefaultOpxHandler):
    def __init__(self, metadata, config, octave_config):
        super().__init__(metadata, config)
        self.octave_config = octave_config

    def create_qmm(self) -> QuantumMachinesManager:
        return QuantumMachinesManager(
            host=self.opx_metadata.host_ip,
            port=self.opx_metadata.port,
            cluster_name=self.opx_metadata.cluster_name,
            octave=self.octave_config,
        )
```

Then in your experiment:

```python
def construct_opx_handler(self):
    return OctaveHandler(self.metadata, self.config, self.octave_config)
```

### Class Reference

| Method | Description |
|--------|-------------|
| `open()` | Get/create QMM, open QuantumMachine |
| `execute(program)` | Execute program, return `OPXContext` |
| `simulate(program, duration, flags, interface)` | Simulate program |
| `close()` | Close the QuantumMachine |
| `get_or_create_qmm()` | Get cached or create new QMM |
| `create_qmm()` | Create new QMM (override to customize) |
| `generate_qua_script(program)` | Generate QUA script string |

---

## CachingOpxHandler

Advanced handler that caches `QuantumMachine` instances based on configuration hash. Use this when running many experiments where only logical parameters change.

> [!IMPORTANT]
> This is an abstract class. You must implement `_split_config()` and `_hash_config()`.

### When to Use

| Scenario | Use DefaultOpxHandler | Use CachingOpxHandler |
|----------|:---------------------:|:---------------------:|
| Different configs each run | Yes | - |
| Same physical setup, varying frequencies | - | Yes |
| Need fresh machine each time | Yes | - |
| Minimize open/close overhead | - | Yes |

### Concept: Config Splitting

The key idea is separating your config into:

1. **Physical config**: Hardware setup that rarely changes (waveforms, mixers, elements)
2. **Logical config**: Parameters that change per-run (frequencies, amplitudes)

The handler caches machines by physical config hash. If the physical config hasn't changed, it reuses the existing machine.

### Implementation

```python
class MyCachingHandler(CachingOpxHandler):
    def _split_config(self, config: dict) -> tuple[dict, dict]:
        """
        Split config into (logical, physical) parts.

        Args:
            config: Full QUA configuration

        Returns:
            Tuple of (logical_config, physical_config)
            - logical_config: Passed to machine.execute() as kwargs
            - physical_config: Used for cache key and machine opening
        """
        # Deep copy to avoid modifying original
        import copy
        config = copy.deepcopy(config)

        # Extract logical parameters
        logical = {}
        for element in config.get("elements", {}).values():
            if "intermediate_frequency" in element:
                logical["if_freq"] = element.pop("intermediate_frequency")

        physical = config
        return logical, physical

    def _hash_config(self, physical_config: dict) -> str:
        """
        Generate hash string for cache lookup.

        Args:
            physical_config: The physical portion of config

        Returns:
            Hash string used as cache key (combined with IP)
        """
        import hashlib
        import json

        # Sort keys for consistent hashing
        config_str = json.dumps(physical_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
```

### Cache Behavior

| `close_on_close` | On `close()` | Use Case |
|------------------|--------------|----------|
| `False` (default) | Machine stays in cache | Reuse across experiments |
| `True` | Machine removed from cache | Fresh machine next time |

```python
# Keep machine cached (default)
handler = MyCachingHandler(metadata, config)

# Remove from cache on close
handler = MyCachingHandler(metadata, config, close_on_close=True)
```

> [!TIP]
> Use `close_on_close=True` when you need to ensure a clean state for each
> experiment, while still benefiting from caching within a single session.

### Cache Structure

```
CachingOpxHandler._cache = {
    ("192.168.1.100", "abc123..."): QuantumMachine,  # IP + config hash
    ("192.168.1.100", "def456..."): QuantumMachine,  # Same IP, different config
    ("192.168.1.101", "abc123..."): QuantumMachine,  # Different IP
}
```

### Logical Config Usage

The logical config returned by `_split_config()` is passed to `machine.execute()`:

```python
# Inside CachingOpxHandler.execute():
job = machine.execute(program, **self._get_execute_kwargs())
# Where _get_execute_kwargs() returns the logical_config
```

This allows runtime parameter overrides without reopening the machine.

### Class Reference

| Method | Description |
|--------|-------------|
| `_split_config(config)` | **Abstract** - Split into (logical, physical) |
| `_hash_config(physical)` | **Abstract** - Generate cache key hash |
| `open()` | Get cached or open new machine |
| `execute(program)` | Execute with logical config kwargs |
| `close()` | Close if `close_on_close=True` |
