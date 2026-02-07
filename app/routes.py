from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template

from app.datastore.base import DataStore

bp = Blueprint("pages", __name__)


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


@bp.route("/")
def index() -> str:
    return render_template("home.html")


@bp.route("/conferences/<conference>")
def conference_years(conference: str) -> str:
    conference_row = _store().get_conference(conference)
    if conference_row is None:
        abort(404)

    proceedings = _store().list_proceedings(conference)
    return render_template(
        "conference_years.html",
        conference=conference_row,
        proceedings=proceedings,
    )


@bp.route("/conferences/<conference>/<year>")
def conference_results(conference: str, year: str) -> str:
    conference_row = _store().get_conference(conference)
    if conference_row is None:
        abort(404)

    results = _store().list_results(conference, year)
    return render_template(
        "conference_results.html",
        conference=conference_row,
        year=year,
        results=results,
    )


def _render_paper_detail(key: str) -> str:
    paper = _store().get_result(key)
    if paper is None:
        abort(404)

    detail_rows: list[dict[str, str]] = []
    for label, verdict_field, text_field in DETAIL_ROWS:
        detail_rows.append(
            {
                "label": label,
                "verdict": _to_verdict(paper.get(verdict_field), verdict_field),
                "evidence": str(paper.get(text_field) or ""),
            }
        )

    return render_template(
        "paper_detail.html",
        paper=paper,
        detail_rows=detail_rows,
    )


@bp.route("/paper/<key>", endpoint="paper_detail")
def paper_detail_singular(key: str) -> str:
    return _render_paper_detail(key)


@bp.route("/papers/<key>", endpoint="paper_detail_plural")
def paper_detail_plural(key: str) -> str:
    return _render_paper_detail(key)


@bp.route("/runs/<run>")
def run_detail(run: str) -> str:
    run_row = _store().get_run(run)
    if run_row is None:
        abort(404)

    return render_template("run_detail.html", run_row=run_row)
