from __future__ import annotations

from pathlib import Path

from flask import Config

from app.datastore.base import DataStore
from app.datastore.sqlite_store import SQLiteDataStore


def build_data_store(config: Config) -> DataStore:
    """Create a data store from app config for backend portability."""
    backend = config.get("DB_BACKEND", "sqlite")
    if backend == "sqlite":
        return SQLiteDataStore(Path(config["SQLITE_DB_PATH"]))
    raise ValueError(f"Unsupported DB_BACKEND: {backend}")
