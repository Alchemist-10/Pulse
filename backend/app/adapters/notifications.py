"""NotificationProvider interface. Declared in Phase 1; implemented in Phase 3.

A notification stores `type` + `params`, never rendered text, and params
carry no clinical data (clinical-safety.md).
"""

from abc import ABC, abstractmethod
from typing import Any


class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, channel: str, address: str, type_: str, params: dict[str, Any]) -> None:
        ...
