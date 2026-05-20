from __future__ import annotations

from flask import current_app

from app.datastore.base import DataStore

RESULT_COLUMN_FIELD_LABELS: list[tuple[str, str]] = [
    ("pseudocode_result", "PC"),
    ("open_source_code_result", "OSC"),
    ("open_datasets_result", "ODS"),
    ("dataset_splits_result", "DS"),
    ("hardware_specification_result", "HS"),
    ("software_dependencies_result", "SD"),
    ("experiment_setup_result", "ES"),
]

RESULT_COLUMN_FIELDS = [field for field, _ in RESULT_COLUMN_FIELD_LABELS]


DETAIL_ROWS = [
    ("Research Type", "research_type_result", "research_type_paper_text"),
    ("Researcher Affiliation", "affiliation_result", "affiliation_paper_text"),
    ("Pseudocode", "pseudocode_result", "pseudocode_paper_text"),
    ("Open Source Code", "open_source_code_result", "open_source_code_paper_text"),
    ("Open Datasets", "open_datasets_result", "open_datasets_paper_text"),
    ("Dataset Splits", "dataset_splits_result", "dataset_splits_paper_text"),
    (
        "Hardware Specification",
        "hardware_specification_result",
        "hardware_specification_paper_text",
    ),
    (
        "Software Dependencies",
        "software_dependencies_result",
        "software_dependencies_paper_text",
    ),
    ("Experiment Setup", "experiment_setup_result", "experiment_setup_paper_text"),
]


def _store() -> DataStore:
    return current_app.extensions["data_store"]


def _to_verdict(value: object, field_name: str | None = None) -> str:
    if field_name == "research_type_result":
        if value in (1, "1", True):
            return "Theoretical"
        if value in (0, "0", False):
            return "Experimental"
    if field_name == "affiliation_result":
        if value in (0, "0"):
            return "Academia"
        if value in (1, "1"):
            return "Collaboration"
        if value in (2, "2"):
            return "Industry"

    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)) and value in (0, 1):
        return "Yes" if int(value) == 1 else "No"
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return "Yes"
        if normalized in {"0", "false", "no"}:
            return "No"
    return str(value)


def _to_binary(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)) and value in (0, 1):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return 1
        if normalized in {"0", "false", "no"}:
            return 0
    return None


def _to_binary_icon(value: object) -> str:
    binary = _to_binary(value)
    if binary is None:
        return "N/A"
    return "✅" if binary == 1 else "❌"


def _to_metric_display(value: object) -> str:
    if value is None:
        return "N/A"
    text = str(value).strip()
    return text if text else "N/A"


def _to_percent_display(value: object) -> str:
    text = _to_metric_display(value)
    if text == "N/A" or text.endswith("%"):
        return text
    return f"{text}%"


def _to_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _to_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None
