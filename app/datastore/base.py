from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

Record = dict[str, Any]


class DataStore(ABC):
    """Read-only interface for pulling website data from a backend."""

    @abstractmethod
    def list_conferences(self) -> list[Record]:
        """Return all conferences."""

    @abstractmethod
    def get_conference(self, conference: str) -> Record | None:
        """Return a conference by slug/code."""

    @abstractmethod
    def list_proceedings(self, conference: str) -> list[Record]:
        """Return proceedings rows for a conference."""

    @abstractmethod
    def list_results(self, conference: str, year: str) -> list[Record]:
        """Return paper results for a conference and year."""

    @abstractmethod
    def get_result(self, key: str) -> Record | None:
        """Return a paper result by key."""

    @abstractmethod
    def get_run(self, run: str) -> Record | None:
        """Return run metadata by run id."""
