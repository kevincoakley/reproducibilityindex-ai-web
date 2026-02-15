from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template

from app.datastore.base import DataStore

bp = Blueprint("pages", __name__)


RESULT_COLUMN_FIELDS = [
    "pseudocode_result",
    "open_source_code_result",
    "open_datasets_result",
    "dataset_splits_result",
    "hardware_specification_result",
    "software_dependencies_result",
    "experiment_setup_result",
]


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


@bp.route("/")
def index() -> str:
    all_proceedings_rows: list[dict[str, object]] = []
    chart_points_by_conference: dict[str, list[dict[str, float]]] = {}
    for row in _store().list_all_proceedings():
        global_mean_raw = row.get("global_mean")
        global_mean_value = _to_float(global_mean_raw)
        global_mean_sort = global_mean_value if global_mean_value is not None else -1.0

        all_proceedings_rows.append(
            {
                "conference": row.get("conference"),
                "year": row.get("year"),
                "number_papers": _to_metric_display(row.get("number_papers")),
                "global_mean": _to_metric_display(global_mean_raw),
                "global_mean_sort": global_mean_sort,
                "global_median": _to_metric_display(row.get("global_median")),
                "documentation_mean": _to_metric_display(row.get("documentation_mean")),
                "dataset_mean": _to_metric_display(row.get("dataset_mean")),
                "code_mean": _to_metric_display(row.get("code_mean")),
                "percent_emperical": _to_percent_display(row.get("percent_emperical")),
                "percent_industry": _to_percent_display(row.get("percent_industry")),
                "url": row.get("url"),
            }
        )

        conference = str(row.get("conference") or "").strip()
        year_value = _to_int(row.get("year"))
        if conference and year_value is not None and global_mean_value is not None:
            chart_points_by_conference.setdefault(conference, []).append(
                {"x": year_value, "y": global_mean_value}
            )

    proceedings: list[dict[str, object]] = []
    seen_conferences: set[str] = set()
    for row in all_proceedings_rows:
        conference = str(row.get("conference") or "")
        if not conference or conference in seen_conferences:
            continue
        seen_conferences.add(conference)
        proceedings.append(row)

    home_chart_datasets = [
        {"label": conference, "data": sorted(points, key=lambda point: point["x"])}
        for conference, points in sorted(chart_points_by_conference.items())
    ]

    return render_template(
        "home.html",
        proceedings=proceedings,
        home_chart_datasets=home_chart_datasets,
    )


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

    proceedings = _store().list_proceedings(conference)
    proceeding_row = next(
        (row for row in proceedings if str(row.get("year")) == year), None
    )
    proceedings_url = (
        str(proceeding_row.get("url"))
        if proceeding_row is not None and proceeding_row.get("url")
        else ""
    )
    proceedings_metrics = _store().get_proceedings_metrics(conference, year) or {}
    metrics = {
        "number_papers": _to_metric_display(proceedings_metrics.get("number_papers")),
        "global_mean": _to_metric_display(proceedings_metrics.get("global_mean")),
        "global_median": _to_metric_display(proceedings_metrics.get("global_median")),
        "documentation_mean": _to_metric_display(
            proceedings_metrics.get("documentation_mean")
        ),
        "dataset_mean": _to_metric_display(proceedings_metrics.get("dataset_mean")),
        "code_mean": _to_metric_display(proceedings_metrics.get("code_mean")),
        "percent_emperical": _to_percent_display(
            proceedings_metrics.get("percent_emperical")
        ),
        "percent_industry": _to_percent_display(
            proceedings_metrics.get("percent_industry")
        ),
    }

    raw_results = _store().list_results(conference, year)
    results: list[dict[str, object]] = []
    for row in raw_results:
        normalized = dict(row)
        total = 0
        for field in RESULT_COLUMN_FIELDS:
            binary_value = _to_binary(row.get(field))
            if binary_value is not None:
                total += binary_value
            normalized[f"{field}_binary"] = (
                binary_value if binary_value is not None else -1
            )
            normalized[f"{field}_icon"] = _to_binary_icon(row.get(field))
        normalized["total"] = total
        results.append(normalized)

    return render_template(
        "conference_results.html",
        conference=conference_row,
        year=year,
        proceedings_url=proceedings_url,
        metrics=metrics,
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
