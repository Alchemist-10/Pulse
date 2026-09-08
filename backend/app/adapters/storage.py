"""StorageProvider interface + the local-filesystem implementation.

Services never call `open()` — they hand bytes to a StorageProvider and
persist the returned path (backend.md). Phase 2 ships the local-disk
provider that writes onto the mounted upload volume; a checksum is the
caller's job (records service), not the store's.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes under `key`; return the storage path to persist."""

    @abstractmethod
    async def get(self, path: str) -> bytes: ...


class LocalStorageProvider(StorageProvider):
    """Writes under a single base directory (the compose upload volume).
    `key` is treated as a relative path; parent dirs are created."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        dest = self._base / key

        def _write() -> None:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

        await asyncio.to_thread(_write)
        return str(dest)

    async def get(self, path: str) -> bytes:
        return await asyncio.to_thread(Path(path).read_bytes)
