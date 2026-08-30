from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from app.datastore.base import DataStore, Record


class SQLiteDataStore(DataStore):
    """SQLite-backed read-only datastore implementation."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        self._percent_metric_columns = self._resolve_percent_metric_columns()

    def _connect(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.create_function(
            "institution_lookup_key", 1, self._institution_lookup_key
        )
        return connection

    @staticmethod
    def _institution_lookup_key(value: object) -> str:
        key = unquote(str(value or ""))
        missing_closing_parentheses = key.count("(") - key.count(")")
        if missing_closing_parentheses > 0:
            key = f"{key}{')' * missing_closing_parentheses}"
        return key

    def _list_columns(self, table_name: str) -> set[str]:
        with self._connect() as connection:
            rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}

    def _resolve_percent_metric_columns(self) -> dict[str, str]:
        columns = self._list_columns("editions_reproducibility_scores")
        metric_suffixes = [
            "",
            "_industry",
            "_pseudocode",
            "_open_source_code",
            "_open_datasets",
            "_dataset_splits",
            "_hardware_specification",
            "_software_dependencies",
            "_experiment_setup",
        ]
        resolved_columns: dict[str, str] = {}
        for suffix in metric_suffixes:
            canonical = f"percent_empirical{suffix}"
            if canonical in columns:
                resolved_columns[canonical] = canonical
            else:
                raise ValueError(
                    "Missing required percent metric column. "
                    f"Expected '{canonical}' "
                    "in editions_reproducibility_scores."
                )
        return resolved_columns

    def _percent_metric_select_list(self, table_alias: str | None = "pm") -> str:
        prefix = f"{table_alias}." if table_alias else ""
        return ",\n                ".join(
            f"{prefix}{source} AS {target}"
            for target, source in self._percent_metric_columns.items()
        )

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
            f"""
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
                {self._percent_metric_select_list("pm")},
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
        return self._fetch_all(f"""
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
                pm.{self._percent_metric_columns["percent_empirical"]} AS percent_empirical,
                pm.{self._percent_metric_columns["percent_empirical_industry"]} AS percent_empirical_industry,
                pm.academia_documentation_score,
                pm.academia_reproducibility_score,
                pm.industry_documentation_score,
                pm.industry_reproducibility_score,
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
                paper_counts.number_papers,
                paper_counts.input_tokens,
                paper_counts.output_tokens
            FROM results AS r
            LEFT JOIN editions AS e
              ON e.venue = r.venue AND e.year = r.year
            LEFT JOIN (
                SELECT
                    venue,
                    year,
                    COUNT(key) AS number_papers,
                    SUM(COALESCE(input_tokens, 0)) AS input_tokens,
                    SUM(COALESCE(thoughts_tokens, 0) + COALESCE(output_tokens, 0)) AS output_tokens
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

    def get_total_input_tokens(self) -> int:
        row = self._fetch_one("""
            SELECT SUM(input_tokens) AS total
            FROM results
            """)
        if row is None:
            return 0
        total = row.get("total")
        if isinstance(total, int):
            return total
        if isinstance(total, (float, str)):
            return int(total)
        return 0

    def get_total_output_tokens(self) -> int:
        row = self._fetch_one("""
            SELECT SUM(COALESCE(thoughts_tokens, 0) + COALESCE(output_tokens, 0)) AS total
            FROM results
            """)
        if row is None:
            return 0
        total = row.get("total")
        if isinstance(total, int):
            return total
        if isinstance(total, (float, str)):
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

    def list_institution_documentation_scores(
        self, min_contributing_papers: int | None = None
    ) -> list[Record]:
        where_clause = ""
        params: tuple[object, ...] = ()
        if min_contributing_papers is not None:
            where_clause = """
            WHERE CAST(ids.contributing_papers AS REAL) >= ?
            """
            params = (min_contributing_papers,)

        return self._fetch_all(
            f"""
            SELECT
                ids.institution_normalized,
                COALESCE(i.title, ids.institution_normalized) AS institution_title,
                ids.total_fractional_documentation_score,
                ids.fractional_paper_count,
                ids.mean_fractional_documentation_score,
                ids.standard_error,
                ids.ci95_lower,
                ids.ci95_upper,
                ids.contributing_papers
            FROM institutions_documentation_scores AS ids
            LEFT JOIN institutions AS i
              ON institution_lookup_key(ids.institution_normalized) = i.key
            {where_clause}
            ORDER BY
              CAST(ids.mean_fractional_documentation_score AS REAL) DESC,
              institution_title ASC
            """,
            params,
        )

    def list_institution_reproducibility_scores(
        self, min_contributing_papers: int | None = None
    ) -> list[Record]:
        where_clause = ""
        params: tuple[object, ...] = ()
        if min_contributing_papers is not None:
            where_clause = """
            WHERE CAST(irs.contributing_papers AS REAL) >= ?
            """
            params = (min_contributing_papers,)

        return self._fetch_all(
            f"""
            SELECT
                irs.institution_normalized,
                COALESCE(i.title, irs.institution_normalized) AS institution_title,
                irs.total_fractional_reproducibility_score,
                irs.fractional_paper_count,
                irs.mean_fractional_reproducibility_score,
                irs.standard_error,
                irs.ci95_lower,
                irs.ci95_upper,
                irs.contributing_papers
            FROM institutions_reproducibility_scores AS irs
            LEFT JOIN institutions AS i
              ON institution_lookup_key(irs.institution_normalized) = i.key
            {where_clause}
            ORDER BY
              CAST(irs.mean_fractional_reproducibility_score AS REAL) DESC,
              institution_title ASC
            """,
            params,
        )

    def get_edition_reproducibility_scores(
        self, venue: str, year: str
    ) -> Record | None:
        return self._fetch_one(
            f"""
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
                {self._percent_metric_columns["percent_empirical"]} AS percent_empirical,
                {self._percent_metric_columns["percent_empirical_industry"]} AS percent_empirical_industry
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
                experiment_setup_paper_text,
                input_tokens,
                thoughts_tokens,
                output_tokens
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

    def list_runs(self) -> list[Record]:
        return self._fetch_all("""
            SELECT run, model
            FROM runs
            ORDER BY run
            """)
