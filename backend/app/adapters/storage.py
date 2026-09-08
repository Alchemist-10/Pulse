"""StorageProvider interface. Declared in Phase 1; implemented in Phase 2.

Services never call `open()` — they hand bytes to a StorageProvider and
store the returned path (backend.md).
"""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes under `key`; return the storage path to persist."""

    @abstractmethod
    async def get(self, path: str) -> bytes:
        ...
