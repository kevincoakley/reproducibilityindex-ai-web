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

    def list_venues(self) -> list[Record]:
        return self._fetch_all("""
            SELECT venue, venue_name, url
            FROM venues
            ORDER BY venue ASC
            """)

    def get_venue(self, venue: str) -> Record | None:
        return self._fetch_one(
            """
            SELECT venue, venue_name, url
            FROM venues
            WHERE venue = ?
            """,
            (venue,),
        )

    def list_editions(self, venue: str) -> list[Record]:
        return self._fetch_all(
            """
            SELECT
                p.venue,
                p.year,
                pm.number_papers,
                pm.reproducibility_score,
                pm.documentation_global_mean,
                pm.documentation_global_median,
                pm.documentation_other_mean,
                pm.documentation_dataset_mean,
                pm.documentation_code_mean,
                pm.percent_emperical,
                pm.percent_industry,
                pm.percent_pseudocode,
                pm.percent_open_source_code,
                pm.percent_open_datasets,
                pm.percent_dataset_splits,
                pm.percent_hardware_specification,
                pm.percent_software_dependencies,
                pm.percent_experiment_setup,
                p.url
            FROM editions AS p
            LEFT JOIN editions_reproducibility_scores AS pm
              ON p.venue = pm.venue AND p.year = pm.year
            WHERE p.venue = ?
            ORDER BY p.year DESC
            """,
            (venue,),
        )

    def list_all_editions(self) -> list[Record]:
        return self._fetch_all("""
            SELECT
                p.venue,
                p.year,
                pm.number_papers,
                pm.reproducibility_score,
                pm.documentation_global_mean,
                pm.documentation_global_median,
                pm.documentation_other_mean,
                pm.documentation_dataset_mean,
                pm.documentation_code_mean,
                pm.percent_emperical,
                pm.percent_industry,
                p.url
            FROM editions AS p
            LEFT JOIN editions_reproducibility_scores AS pm
              ON p.venue = pm.venue AND p.year = pm.year
            ORDER BY p.venue ASC, p.year DESC
            """)

    def list_paper_counts_by_venue_and_year(self) -> list[Record]:
        return self._fetch_all("""
            SELECT
                e.venue,
                e.year,
                COUNT(r.key) AS number_papers
            FROM editions AS e
            LEFT JOIN results AS r
              ON e.venue = r.venue AND e.year = r.year
            GROUP BY e.venue, e.year
            ORDER BY e.year ASC, e.venue ASC
            """)

    def list_data_rows(self) -> list[Record]:
        return self._fetch_all("""
            SELECT DISTINCT
                r.venue,
                r.year,
                r.run,
                e.url,
                paper_counts.number_papers
            FROM results AS r
            LEFT JOIN editions AS e
              ON e.venue = r.venue AND e.year = r.year
            LEFT JOIN (
                SELECT
                    venue,
                    year,
                    COUNT(key) AS number_papers
                FROM results
                GROUP BY venue, year
            ) AS paper_counts
              ON paper_counts.venue = r.venue AND paper_counts.year = r.year
            ORDER BY r.run DESC, r.year DESC, r.venue ASC
            """)

    def list_venue_stats(self) -> list[Record]:
        return self._fetch_all("""
            SELECT venue, total
            FROM venue_stats
            ORDER BY CAST(total AS INTEGER) DESC, venue ASC
            """)

    def list_year_stats(self) -> list[Record]:
        return self._fetch_all("""
            SELECT year, total
            FROM year_stats
            ORDER BY CAST(year AS INTEGER) ASC
            """)

    def get_total_papers_count(self) -> int:
        row = self._fetch_one("""
            SELECT COUNT(key) AS total_papers
            FROM results
            """)
        if row is None:
            return 0
        total = row.get("total_papers")
        if isinstance(total, int):
            return total
        if isinstance(total, str):
            return int(total)
        return 0

    def list_country_documentation_scores(self) -> list[Record]:
        return self._fetch_all("""
            SELECT
                c.country,
                c.name,
                c.flag,
                crs.total_fractional_documentation_score,
                crs.fractional_paper_count,
                crs.mean_fractional_documentation_score,
                crs.standard_error,
                crs.ci95_lower,
                crs.ci95_upper,
                crs.contributing_papers
            FROM countries AS c
            JOIN countries_documentation_scores AS crs
              ON c.country = crs.country
            ORDER BY
              CAST(crs.mean_fractional_documentation_score AS REAL) DESC,
              c.name ASC
            """)

    def list_country_reproducibility_scores(self) -> list[Record]:
        return self._fetch_all("""
            SELECT
                c.country,
                c.name,
                c.flag,
                crs.total_fractional_reproducibility_score,
                crs.fractional_paper_count,
                crs.mean_fractional_reproducibility_score,
                crs.standard_error,
                crs.ci95_lower,
                crs.ci95_upper,
                crs.contributing_papers
            FROM countries AS c
            JOIN countries_reproducibility_scores AS crs
              ON c.country = crs.country
            ORDER BY
              CAST(crs.mean_fractional_reproducibility_score AS REAL) DESC,
              c.name ASC
            """)

    def get_edition_reproducibility_scores(
        self, venue: str, year: str
    ) -> Record | None:
        return self._fetch_one(
            """
            SELECT
                venue,
                year,
                number_papers,
                reproducibility_score,
                documentation_global_mean,
                documentation_global_median,
                documentation_other_mean,
                documentation_dataset_mean,
                documentation_code_mean,
                percent_emperical,
                percent_industry
            FROM editions_reproducibility_scores
            WHERE venue = ? AND year = ?
            """,
            (venue, year),
        )

    def list_results(self, venue: str, year: str) -> list[Record]:
        return self._fetch_all(
            """
            SELECT
                key,
                title,
                authors,
                venue,
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
            WHERE venue = ? AND year = ?
            ORDER BY title ASC
            """,
            (venue, year),
        )

    def get_result(self, key: str) -> Record | None:
        return self._fetch_one(
            """
            SELECT
                key,
                title,
                authors,
                venue,
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
