# Handlers

Hardware lifecycle management (open/close).

## DefaultOpxHandler

Standard handler with QMM caching per IP address.

```python
def construct_opx_handler(self):
    return DefaultOpxHandler(self.metadata, self.config)
```

**Features:**
- Caches `QuantumMachinesManager` per IP (avoids reconnection)
- Override `create_qmm()` for custom setup (e.g., Octave)

## CachingOpxHandler

Advanced handler that caches machines by config hash.

```python
class MyCachingHandler(CachingOpxHandler):
    def _split_config(self, config):
        # Return (logical_config, physical_config)
        pass

    def _hash_config(self, physical_config):
        # Return hash string for cache key
        pass
```

**Features:**
- Avoids reopening machines when physical config unchanged
- Splits config into logical (per-run) and physical (cached) parts
- Set `close_on_close=True` to remove from cache on close
