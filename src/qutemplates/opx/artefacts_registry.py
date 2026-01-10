from typing import Any


class ArtefactRegistry:
    def __init__(self):
        self._db: dict = {}

    def register(self, key: str, data: Any):
        if self._db.get(key) is not None:
            raise ValueError(f"Trying to overwrite register with key: {key}")
        self._db[key] = data

    def get(self, key: str, default=None) -> Any:
        """Get artifact data by key."""
        return self._db.get(key, default)

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._db

    def export(self) -> dict:
        return self._db

    def reset(self):
        self._db = {}
