from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.datastore.base import DataStore, Record


class SQLiteDataStore(DataStore):
    """SQLite-backed read-only datastore implementation."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()

    def _connect(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def _fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[Record]:
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def _fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> Record | None:
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row is not None else None

    def list_conferences(self) -> list[Record]:
        return self._fetch_all("""
            SELECT conference, conference_name, url
            FROM conferences
            ORDER BY conference ASC
            """)

    def get_conference(self, conference: str) -> Record | None:
        return self._fetch_one(
            """
            SELECT conference, conference_name, url
            FROM conferences
            WHERE conference = ?
            """,
            (conference,),
        )

    def list_proceedings(self, conference: str) -> list[Record]:
        return self._fetch_all(
            """
            SELECT conference, year, number_papers, url
            FROM proceedings
            WHERE conference = ?
            ORDER BY year DESC
            """,
            (conference,),
        )

    def list_results(self, conference: str, year: str) -> list[Record]:
        return self._fetch_all(
            """
            SELECT
                key,
                title,
                authors,
                conference,
                year,
                run,
                pdf_url,
                research_type_result,
                research_type_paper_text,
                affiliation_result,
                affiliation_paper_text,
                pseudocode_result,
                pseudocode_paper_text,
                open_source_code_result,
                open_source_code_paper_text,
                open_datasets_result,
                open_datasets_paper_text,
                dataset_splits_result,
                dataset_splits_paper_text,
                hardware_specification_result,
                hardware_specification_paper_text,
                software_dependencies_result,
                software_dependencies_paper_text,
                experiment_setup_result,
                experiment_setup_paper_text
            FROM results
            WHERE conference = ? AND year = ?
            ORDER BY title ASC
            """,
            (conference, year),
        )

    def get_result(self, key: str) -> Record | None:
        return self._fetch_one(
            """
            SELECT
                key,
                title,
                authors,
                conference,
                year,
                run,
                pdf_url,
                research_type_result,
                research_type_paper_text,
                affiliation_result,
                affiliation_paper_text,
                pseudocode_result,
                pseudocode_paper_text,
                open_source_code_result,
                open_source_code_paper_text,
                open_datasets_result,
                open_datasets_paper_text,
                dataset_splits_result,
                dataset_splits_paper_text,
                hardware_specification_result,
                hardware_specification_paper_text,
                software_dependencies_result,
                software_dependencies_paper_text,
                experiment_setup_result,
                experiment_setup_paper_text
            FROM results
            WHERE key = ?
            """,
            (key,),
        )

    def get_run(self, run: str) -> Record | None:
        return self._fetch_one(
            """
            SELECT run, model, prompt, questions, temperature, top_p
            FROM runs
            WHERE run = ?
            """,
            (run,),
        )
