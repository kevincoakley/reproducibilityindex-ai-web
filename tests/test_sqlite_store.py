from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from flask import Flask

from app.datastore import build_data_store
from app.datastore.sqlite_store import SQLiteDataStore


def _create_scores_table(db_path: Path, percent_prefix: str) -> None:
    connection = sqlite3.connect(db_path)
    connection.execute(f"""
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
            {percent_prefix} REAL,
            {percent_prefix}_industry REAL,
            {percent_prefix}_pseudocode REAL,
            {percent_prefix}_open_source_code REAL,
            {percent_prefix}_open_datasets REAL,
            {percent_prefix}_dataset_splits REAL,
            {percent_prefix}_hardware_specification REAL,
            {percent_prefix}_software_dependencies REAL,
            {percent_prefix}_experiment_setup REAL
        )
        """)
    connection.execute("""
        CREATE TABLE editions (
            venue TEXT,
            year TEXT,
            url TEXT
        )
        """)
    connection.execute("""
        CREATE TABLE results (
            key TEXT
        )
        """)
    connection.execute(f"""
        INSERT INTO editions_reproducibility_scores VALUES (
            'CONF',
            '2025',
            10,
            0.75,
            0.61,
            0.62,
            0.50,
            0.71,
            0.82,
            78.0,
            22.0,
            60.0,
            63.0,
            66.0,
            69.0,
            72.0,
            75.0,
            78.0
        )
        """)
    connection.execute(
        "INSERT INTO editions VALUES ('CONF', '2025', 'https://example.org')"
    )
    connection.execute("INSERT INTO results VALUES ('paper-1')")
    connection.commit()
    connection.close()


def test_list_editions_uses_canonical_percent_keys_with_canonical_schema(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "canonical.sqlite"
    _create_scores_table(db_path, "percent_empirical")
    store = SQLiteDataStore(db_path)

    row = store.list_editions("CONF")[0]

    assert row["percent_empirical"] == 78.0
    assert row["percent_empirical_industry"] == 22.0
    assert row["percent_empirical_pseudocode"] == 60.0
    assert row["percent_empirical_experiment_setup"] == 78.0


def test_store_fails_fast_when_percent_columns_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "invalid.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("""
        CREATE TABLE editions_reproducibility_scores (
            venue TEXT,
            year TEXT
        )
        """)
    connection.commit()
    connection.close()

    with pytest.raises(ValueError, match="Missing required percent metric column"):
        SQLiteDataStore(db_path)


def test_store_fails_fast_with_legacy_percent_column_names(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    _create_scores_table(db_path, "percent_emperical")

    with pytest.raises(ValueError, match="Expected 'percent_empirical'"):
        SQLiteDataStore(db_path)


def test_connect_is_read_only(tmp_path: Path) -> None:
    db_path = tmp_path / "readonly.sqlite"
    _create_scores_table(db_path, "percent_empirical")
    store = SQLiteDataStore(db_path)

    with pytest.raises(sqlite3.OperationalError):
        with store._connect() as connection:  # noqa: SLF001
            connection.execute("CREATE TABLE write_attempt (id INTEGER)")


def test_get_total_papers_count_handles_non_integer_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "counts.sqlite"
    _create_scores_table(db_path, "percent_empirical")
    store = SQLiteDataStore(db_path)

    assert store.get_total_papers_count() == 1
    store._fetch_one = lambda *_args, **_kwargs: {"total_papers": "5"}  # type: ignore[method-assign]
    assert store.get_total_papers_count() == 5
    store._fetch_one = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    assert store.get_total_papers_count() == 0


def test_build_data_store_rejects_unsupported_backend() -> None:
    app = Flask(__name__)
    app.config.update(
        {
            "DB_BACKEND": "postgres",
            "SQLITE_DB_PATH": "results.sqlite",
        }
    )

    with pytest.raises(ValueError, match="Unsupported DB_BACKEND"):
        build_data_store(app.config)
