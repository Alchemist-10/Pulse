"""Records DI hooks.

`get_storage_provider` is overridden onto a tmp dir in tests; in
production it points at the mounted upload volume (`PULSE_UPLOAD_DIR`,
default `/data/uploads`).
"""

import os

from app.adapters.storage import LocalStorageProvider, StorageProvider

_UPLOAD_DIR = os.environ.get("PULSE_UPLOAD_DIR", "/data/uploads")


def get_storage_provider() -> StorageProvider:
    return LocalStorageProvider(_UPLOAD_DIR)
