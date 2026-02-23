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
    all_edition_rows: list[dict[str, object]] = []
    chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    for row in _store().list_all_editions():
        global_mean_raw = row.get("global_mean")
        global_mean_value = _to_float(global_mean_raw)
        global_mean_sort = global_mean_value if global_mean_value is not None else -1.0

        all_edition_rows.append(
            {
                "venue": row.get("venue"),
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

        venue = str(row.get("venue") or "").strip()
        year_value = _to_int(row.get("year"))
        if venue and year_value is not None and global_mean_value is not None:
            chart_points_by_venue.setdefault(venue, []).append(
                {"x": year_value, "y": global_mean_value}
            )

    editions: list[dict[str, object]] = []
    seen_venues: set[str] = set()
    for row in all_edition_rows:
        venue = str(row.get("venue") or "")
        if not venue or venue in seen_venues:
            continue
        seen_venues.add(venue)
        editions.append(row)

    home_chart_datasets = [
        {"label": venue, "data": sorted(points, key=lambda point: point["x"])}
        for venue, points in sorted(chart_points_by_venue.items())
    ]

    return render_template(
        "home.html",
        editions=editions,
        home_chart_datasets=home_chart_datasets,
    )


@bp.route("/countries/")
def countries() -> str:
    rows = _store().list_country_reproducibility_scores()
    countries_rows: list[dict[str, object]] = []
    countries_chart_labels: list[str] = []
    countries_chart_data: list[dict[str, object]] = []

    for row in rows:
        mean_value = _to_float(row.get("mean_fractional_reproducibility_score"))
        ci95_lower_value = _to_float(row.get("ci95_lower"))
        ci95_upper_value = _to_float(row.get("ci95_upper"))
        total_value = _to_float(row.get("total_fractional_reproducibility_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        standard_error_value = _to_float(row.get("standard_error"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))
        mean_sort = mean_value if mean_value is not None else -1.0
        flag = str(row.get("flag") or "").strip()

        country_row = {
            "name": _to_metric_display(row.get("name")),
            "country": _to_metric_display(row.get("country")),
            "flag": flag if flag else "N/A",
            "total_fractional_reproducibility_score": _to_metric_display(
                row.get("total_fractional_reproducibility_score")
            ),
            "fractional_paper_count": _to_metric_display(
                row.get("fractional_paper_count")
            ),
            "mean_fractional_reproducibility_score": _to_metric_display(
                row.get("mean_fractional_reproducibility_score")
            ),
            "standard_error": _to_metric_display(row.get("standard_error")),
            "contributing_papers": _to_metric_display(row.get("contributing_papers")),
            "mean_sort": mean_sort,
            "total_sort": total_value if total_value is not None else -1.0,
            "fractional_paper_count_sort": (
                fractional_paper_count_value
                if fractional_paper_count_value is not None
                else -1.0
            ),
            "standard_error_sort": (
                standard_error_value if standard_error_value is not None else -1.0
            ),
            "contributing_papers_sort": (
                contributing_papers_value
                if contributing_papers_value is not None
                else -1.0
            ),
        }
        countries_rows.append(country_row)

        if mean_value is None:
            continue

        lower_bound = ci95_lower_value if ci95_lower_value is not None else mean_value
        upper_bound = ci95_upper_value if ci95_upper_value is not None else mean_value
        countries_chart_labels.append(flag if flag else country_row["name"])
        countries_chart_data.append(
            {
                "x": mean_value,
                "xMin": lower_bound,
                "xMax": upper_bound,
                "countryName": country_row["name"],
            }
        )

    countries_chart_height = max(420, min(2200, len(countries_chart_data) * 33))
    return render_template(
        "countries.html",
        countries_rows=countries_rows,
        countries_chart_labels=countries_chart_labels,
        countries_chart_data=countries_chart_data,
        countries_chart_height=countries_chart_height,
    )


@bp.route("/data/")
def data() -> str:
    rows = _store().list_paper_counts_by_venue_and_year()
    chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    for row in rows:
        venue = str(row.get("venue") or "").strip()
        year_value = _to_int(row.get("year"))
        paper_count_value = _to_int(row.get("number_papers"))
        if not venue or year_value is None or paper_count_value is None:
            continue
        chart_points_by_venue.setdefault(venue, []).append(
            {"x": year_value, "y": paper_count_value}
        )

    data_chart_datasets = [
        {"label": venue, "data": sorted(points, key=lambda point: point["x"])}
        for venue, points in sorted(chart_points_by_venue.items())
    ]
    data_rows = [
        {
            "venue": row.get("venue"),
            "year": row.get("year"),
            "number_papers": _to_metric_display(row.get("number_papers")),
            "run": _to_metric_display(row.get("run")),
            "url": row.get("url"),
        }
        for row in _store().list_data_rows()
    ]
    return render_template(
        "data.html", data_chart_datasets=data_chart_datasets, data_rows=data_rows
    )


@bp.route("/venues/<venue>")
def venue_years(venue: str) -> str:
    venue_row = _store().get_venue(venue)
    if venue_row is None:
        abort(404)

    editions = _store().list_editions(venue)
    percentage_metric_fields = [
        "percent_pseudocode",
        "percent_open_source_code",
        "percent_open_datasets",
        "percent_dataset_splits",
        "percent_hardware_specification",
        "percent_software_dependencies",
        "percent_experiment_setup",
    ]
    venue_chart_datasets: list[dict[str, object]] = []
    for field in percentage_metric_fields:
        metric_points: list[dict[str, float]] = []
        for row in editions:
            year_value = _to_int(row.get("year"))
            percent_value = _to_float(row.get(field))
            if year_value is None or percent_value is None:
                continue
            metric_points.append({"x": year_value, "y": percent_value})
        label = " ".join(
            word.capitalize() for word in field.removeprefix("percent_").split("_")
        )
        venue_chart_datasets.append(
            {
                "label": label,
                "data": sorted(metric_points, key=lambda point: point["x"]),
            }
        )
    return render_template(
        "venue_years.html",
        venue=venue_row,
        editions=editions,
        venue_chart_datasets=venue_chart_datasets,
    )


@bp.route("/venues/<venue>/<year>")
def venue_results(venue: str, year: str) -> str:
    venue_row = _store().get_venue(venue)
    if venue_row is None:
        abort(404)

    editions = _store().list_editions(venue)
    edition_row = next((row for row in editions if str(row.get("year")) == year), None)
    edition_url = (
        str(edition_row.get("url"))
        if edition_row is not None and edition_row.get("url")
        else ""
    )
    reproducibility_scores = (
        _store().get_edition_reproducibility_scores(venue, year) or {}
    )
    metrics = {
        "number_papers": _to_metric_display(
            reproducibility_scores.get("number_papers")
        ),
        "global_mean": _to_metric_display(reproducibility_scores.get("global_mean")),
        "global_median": _to_metric_display(
            reproducibility_scores.get("global_median")
        ),
        "documentation_mean": _to_metric_display(
            reproducibility_scores.get("documentation_mean")
        ),
        "dataset_mean": _to_metric_display(reproducibility_scores.get("dataset_mean")),
        "code_mean": _to_metric_display(reproducibility_scores.get("code_mean")),
        "percent_emperical": _to_percent_display(
            reproducibility_scores.get("percent_emperical")
        ),
        "percent_industry": _to_percent_display(
            reproducibility_scores.get("percent_industry")
        ),
    }

    raw_results = _store().list_results(venue, year)
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
        "venue_results.html",
        venue=venue_row,
        year=year,
        edition_url=edition_url,
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
