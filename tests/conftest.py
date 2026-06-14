"""
Session-scoped fixture that ensures results.sqlite exists.

When running locally the real database is used. In CI (or any environment
where the file is absent) a minimal fixture database is created so that all
route and datastore tests can run without the production data file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "results.sqlite"


def _build_fixture_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript("""
        DROP TABLE IF EXISTS venues;
        DROP TABLE IF EXISTS editions;
        DROP TABLE IF EXISTS editions_reproducibility_scores;
        DROP TABLE IF EXISTS runs;
        DROP TABLE IF EXISTS results;
        DROP TABLE IF EXISTS countries;
        DROP TABLE IF EXISTS countries_documentation_scores;
        DROP TABLE IF EXISTS countries_reproducibility_scores;
        DROP TABLE IF EXISTS institutions;
        DROP TABLE IF EXISTS institutions_documentation_scores;
        DROP TABLE IF EXISTS institutions_reproducibility_scores;
        DROP TABLE IF EXISTS venue_stats;
        DROP TABLE IF EXISTS year_stats;

        CREATE TABLE venues (
            venue TEXT PRIMARY KEY,
            venue_name TEXT,
            url TEXT
        );

        CREATE TABLE editions (
            venue TEXT,
            year TEXT,
            url TEXT
        );

        CREATE TABLE editions_reproducibility_scores (
            venue TEXT,
            year TEXT,
            number_papers INTEGER,
            reproducibility_score REAL,
            documentation_global_mean REAL,
            documentation_global_median REAL,
            documentation_other_mean REAL,
            documentation_dataset_mean REAL,
            documentation_code_mean REAL,
            percent_empirical REAL,
            percent_empirical_industry REAL,
            percent_empirical_pseudocode REAL,
            percent_empirical_open_source_code REAL,
            percent_empirical_open_datasets REAL,
            percent_empirical_dataset_splits REAL,
            percent_empirical_hardware_specification REAL,
            percent_empirical_software_dependencies REAL,
            percent_empirical_experiment_setup REAL,
            academia_documentation_score REAL,
            academia_reproducibility_score REAL,
            industry_documentation_score REAL,
            industry_reproducibility_score REAL
        );

        CREATE TABLE runs (
            run TEXT PRIMARY KEY,
            model TEXT,
            prompt TEXT,
            questions TEXT,
            temperature REAL,
            top_p REAL
        );

        CREATE TABLE results (
            key TEXT,
            title TEXT,
            authors TEXT,
            venue TEXT,
            year TEXT,
            run TEXT,
            pdf_url TEXT,
            research_type_result INTEGER,
            research_type_paper_text TEXT,
            affiliation_result INTEGER,
            affiliation_paper_text TEXT,
            pseudocode_result INTEGER,
            pseudocode_paper_text TEXT,
            open_source_code_result INTEGER,
            open_source_code_paper_text TEXT,
            open_datasets_result INTEGER,
            open_datasets_paper_text TEXT,
            dataset_splits_result INTEGER,
            dataset_splits_paper_text TEXT,
            hardware_specification_result INTEGER,
            hardware_specification_paper_text TEXT,
            software_dependencies_result INTEGER,
            software_dependencies_paper_text TEXT,
            experiment_setup_result INTEGER,
            experiment_setup_paper_text TEXT,
            input_tokens INTEGER,
            thoughts_tokens INTEGER,
            output_tokens INTEGER
        );

        CREATE TABLE countries (
            country TEXT PRIMARY KEY,
            name TEXT,
            flag TEXT
        );

        CREATE TABLE countries_documentation_scores (
            country TEXT,
            venue TEXT,
            year TEXT,
            total_fractional_documentation_score REAL,
            fractional_paper_count REAL,
            mean_fractional_documentation_score REAL,
            standard_error REAL,
            ci95_lower REAL,
            ci95_upper REAL,
            contributing_papers INTEGER
        );

        CREATE TABLE countries_reproducibility_scores (
            country TEXT,
            total_fractional_reproducibility_score REAL,
            fractional_paper_count REAL,
            mean_fractional_reproducibility_score REAL,
            standard_error REAL,
            ci95_lower REAL,
            ci95_upper REAL,
            contributing_papers INTEGER
        );

        CREATE TABLE institutions (
            key TEXT PRIMARY KEY,
            title TEXT
        );

        CREATE TABLE institutions_documentation_scores (
            institution_normalized TEXT,
            total_fractional_documentation_score REAL,
            fractional_paper_count REAL,
            mean_fractional_documentation_score REAL,
            standard_error REAL,
            ci95_lower REAL,
            ci95_upper REAL,
            contributing_papers INTEGER
        );

        CREATE TABLE institutions_reproducibility_scores (
            institution_normalized TEXT,
            total_fractional_reproducibility_score REAL,
            fractional_paper_count REAL,
            mean_fractional_reproducibility_score REAL,
            standard_error REAL,
            ci95_lower REAL,
            ci95_upper REAL,
            contributing_papers INTEGER
        );

        CREATE TABLE venue_stats (
            venue TEXT,
            total INTEGER
        );

        CREATE TABLE year_stats (
            year TEXT,
            total INTEGER
        );
    """)

    con.execute(
        "INSERT INTO venues VALUES (?, ?, ?)",
        ("VENUE", "Test Venue", "https://example.com"),
    )
    con.execute(
        "INSERT INTO editions VALUES (?, ?, ?)",
        ("VENUE", "2024", "https://example.com/2024"),
    )
    con.execute(
        """INSERT INTO editions_reproducibility_scores VALUES
           (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "VENUE",
            "2024",
            1,
            0.5,
            0.6,
            0.5,
            0.4,
            0.3,
            0.7,
            0.8,
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            4.0,
            0.65,
            3.8,
            0.52,
        ),
    )
    con.execute(
        "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)",
        ("run-001", "test-model", "Test prompt.", "Test questions.", 0.0, 1.0),
    )
    con.execute(
        """INSERT INTO results VALUES
           (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "test-paper-key",
            "A Test Paper",
            "Author One",
            "VENUE",
            "2024",
            "run-001",
            "https://example.com/paper.pdf",
            0,
            "Experimental",
            0,
            "Academia",
            0,
            "No pseudocode.",
            0,
            "No open source code.",
            0,
            "No open datasets.",
            0,
            "No dataset splits.",
            0,
            "No hardware specification.",
            0,
            "No software dependencies.",
            0,
            "No experiment setup.",
            150000,
            30000,
            20000,
        ),
    )
    con.execute(
        "INSERT INTO countries VALUES (?, ?, ?)",
        ("AT", "Austria", "🇦🇹"),
    )
    con.execute(
        """INSERT INTO countries_documentation_scores VALUES
           (?,?,?,?,?,?,?,?,?,?)""",
        ("AT", "VENUE", "2024", 0.6, 1.0, 0.6, 0.05, 0.5, 0.7, 1),
    )
    con.execute(
        "INSERT INTO countries_reproducibility_scores VALUES (?,?,?,?,?,?,?,?)",
        ("AT", 0.5, 1.0, 0.5, 0.05, 0.4, 0.6, 1),
    )
    con.execute(
        "INSERT INTO institutions VALUES (?, ?)",
        ("TU Wien", "TU Wien"),
    )
    con.execute(
        """INSERT INTO institutions_documentation_scores VALUES
           (?,?,?,?,?,?,?,?)""",
        ("TU Wien", 60.0, 100.0, 0.6, 0.02, 0.56, 0.64, 100),
    )
    con.execute(
        """INSERT INTO institutions_reproducibility_scores VALUES
           (?,?,?,?,?,?,?,?)""",
        ("TU Wien", 50.0, 100.0, 0.5, 0.02, 0.46, 0.54, 100),
    )
    con.execute("INSERT INTO venue_stats VALUES (?, ?)", ("VENUE", 1))
    con.execute("INSERT INTO year_stats VALUES (?, ?)", ("2024", 1))

    con.commit()
    con.close()


def _fixture_db_is_stale(path: Path) -> bool:
    """Return True if the database is missing required columns added recently."""
    try:
        con = sqlite3.connect(path)
        cols = {row[1] for row in con.execute("PRAGMA table_info(results)")}
        con.close()
        return not {"input_tokens", "thoughts_tokens", "output_tokens"}.issubset(cols)
    except Exception:
        return True


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database() -> None:
    """Create a minimal fixture database when results.sqlite is absent, empty, or stale."""
    if (
        not DB_PATH.exists()
        or DB_PATH.stat().st_size == 0
        or _fixture_db_is_stale(DB_PATH)
    ):
        _build_fixture_db(DB_PATH)
