from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

Record = dict[str, Any]


class DataStore(ABC):
    """Read-only interface for pulling website data from a backend."""

    @abstractmethod
    def list_venues(self) -> list[Record]:
        """Return all venues."""

    @abstractmethod
    def get_venue(self, venue: str) -> Record | None:
        """Return a venue by slug/code."""

    @abstractmethod
    def list_editions(self, venue: str) -> list[Record]:
        """Return edition rows for a venue."""

    @abstractmethod
    def list_all_editions(self) -> list[Record]:
        """Return edition rows across all venues."""

    @abstractmethod
    def list_paper_counts_by_venue_and_year(self) -> list[Record]:
        """Return paper counts grouped by venue and year."""

    @abstractmethod
    def list_data_rows(self) -> list[Record]:
        """Return /data table rows with run, venue, year, counts, and URL."""

    @abstractmethod
    def list_venue_stats(self) -> list[Record]:
        """Return venue totals from venue_stats."""

    @abstractmethod
    def list_year_stats(self) -> list[Record]:
        """Return year totals from year_stats."""

    @abstractmethod
    def get_total_papers_count(self) -> int:
        """Return the total number of papers in results."""

    @abstractmethod
    def list_country_reproducibility_scores(self) -> list[Record]:
        """Return joined country reproducibility score rows."""

    @abstractmethod
    def get_edition_reproducibility_scores(
        self, venue: str, year: str
    ) -> Record | None:
        """Return reproducibility score metrics for a venue edition year."""

    @abstractmethod
    def list_results(self, venue: str, year: str) -> list[Record]:
        """Return paper results for a venue and year."""

    @abstractmethod
    def get_result(self, key: str) -> Record | None:
        """Return a paper result by key."""

    @abstractmethod
    def get_run(self, run: str) -> Record | None:
        """Return run metadata by run id."""
