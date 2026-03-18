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
    doc_mean_chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    repro_score_chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    for row in _store().list_all_editions():
        documentation_global_mean_raw = row.get("documentation_global_mean")
        documentation_global_mean_value = _to_float(documentation_global_mean_raw)
        reproducibility_score_value = _to_float(row.get("reproducibility_score"))
        documentation_global_mean_sort = (
            documentation_global_mean_value
            if documentation_global_mean_value is not None
            else -1.0
        )

        all_edition_rows.append(
            {
                "venue": row.get("venue"),
                "year": row.get("year"),
                "number_papers": _to_metric_display(row.get("number_papers")),
                "reproducibility_score": _to_metric_display(
                    row.get("reproducibility_score")
                ),
                "documentation_global_mean": _to_metric_display(
                    documentation_global_mean_raw
                ),
                "documentation_global_mean_sort": documentation_global_mean_sort,
                "documentation_global_median": _to_metric_display(
                    row.get("documentation_global_median")
                ),
                "documentation_other_mean": _to_metric_display(
                    row.get("documentation_other_mean")
                ),
                "documentation_dataset_mean": _to_metric_display(
                    row.get("documentation_dataset_mean")
                ),
                "documentation_code_mean": _to_metric_display(
                    row.get("documentation_code_mean")
                ),
                "percent_empirical": _to_percent_display(row.get("percent_empirical")),
                "percent_empirical_industry": _to_percent_display(
                    row.get("percent_empirical_industry")
                ),
                "url": row.get("url"),
            }
        )

        venue = str(row.get("venue") or "").strip()
        year_value = _to_int(row.get("year"))
        if (
            venue
            and year_value is not None
            and documentation_global_mean_value is not None
        ):
            doc_mean_chart_points_by_venue.setdefault(venue, []).append(
                {"x": year_value, "y": documentation_global_mean_value}
            )
        if venue and year_value is not None and reproducibility_score_value is not None:
            repro_score_chart_points_by_venue.setdefault(venue, []).append(
                {"x": year_value, "y": reproducibility_score_value}
            )

    editions: list[dict[str, object]] = []
    seen_venues: set[str] = set()
    for row in all_edition_rows:
        venue = str(row.get("venue") or "")
        if not venue or venue in seen_venues:
            continue
        seen_venues.add(venue)
        editions.append(row)

    home_doc_mean_chart_datasets = [
        {"label": venue, "data": sorted(points, key=lambda point: point["x"])}
        for venue, points in sorted(doc_mean_chart_points_by_venue.items())
    ]
    home_repro_score_chart_datasets = [
        {"label": venue, "data": sorted(points, key=lambda point: point["x"])}
        for venue, points in sorted(repro_score_chart_points_by_venue.items())
    ]

    return render_template(
        "home.html",
        editions=editions,
        home_doc_mean_chart_datasets=home_doc_mean_chart_datasets,
        home_repro_score_chart_datasets=home_repro_score_chart_datasets,
    )


@bp.route("/countries/")
def countries() -> str:
    documentation_rows = _store().list_country_documentation_scores()
    reproducibility_rows = _store().list_country_reproducibility_scores()
    countries_rows: list[dict[str, object]] = []
    countries_doc_chart_labels: list[str] = []
    countries_doc_chart_data: list[dict[str, object]] = []
    countries_repro_chart_labels: list[str] = []
    countries_repro_chart_data: list[dict[str, object]] = []
    reproducibility_by_country = {
        str(row.get("country") or ""): row for row in reproducibility_rows
    }

    def _build_country_chart(
        rows: list[dict[str, object]],
        mean_field_name: str,
        labels: list[str],
        data: list[dict[str, object]],
    ) -> None:
        for row in rows:
            mean_value = _to_float(row.get(mean_field_name))
            if mean_value is None:
                continue

            ci95_lower_value = _to_float(row.get("ci95_lower"))
            ci95_upper_value = _to_float(row.get("ci95_upper"))
            lower_bound = (
                ci95_lower_value if ci95_lower_value is not None else mean_value
            )
            upper_bound = (
                ci95_upper_value if ci95_upper_value is not None else mean_value
            )
            flag = str(row.get("flag") or "").strip()
            country_name = _to_metric_display(row.get("name"))

            labels.append(flag if flag else country_name)
            data.append(
                {
                    "x": mean_value,
                    "xMin": lower_bound,
                    "xMax": upper_bound,
                    "countryName": country_name,
                }
            )

    for row in documentation_rows:
        country_code = str(row.get("country") or "")
        reproducibility_row = reproducibility_by_country.get(country_code, {})
        mean_repro_value = _to_float(
            reproducibility_row.get("mean_fractional_reproducibility_score")
        )
        mean_doc_value = _to_float(row.get("mean_fractional_documentation_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))
        mean_repro_sort = mean_repro_value if mean_repro_value is not None else -1.0
        mean_doc_sort = mean_doc_value if mean_doc_value is not None else -1.0
        flag = str(row.get("flag") or "").strip()

        country_row = {
            "name": _to_metric_display(row.get("name")),
            "country": _to_metric_display(country_code),
            "flag": flag if flag else "N/A",
            "mean_fractional_reproducibility_score": _to_metric_display(
                reproducibility_row.get("mean_fractional_reproducibility_score")
            ),
            "mean_fractional_documentation_score": _to_metric_display(
                row.get("mean_fractional_documentation_score")
            ),
            "fractional_paper_count": _to_metric_display(
                row.get("fractional_paper_count")
            ),
            "contributing_papers": _to_metric_display(row.get("contributing_papers")),
            "mean_repro_sort": mean_repro_sort,
            "mean_doc_sort": mean_doc_sort,
            "fractional_paper_count_sort": (
                fractional_paper_count_value
                if fractional_paper_count_value is not None
                else -1.0
            ),
            "contributing_papers_sort": (
                contributing_papers_value
                if contributing_papers_value is not None
                else -1.0
            ),
        }
        countries_rows.append(country_row)

    _build_country_chart(
        documentation_rows,
        "mean_fractional_documentation_score",
        countries_doc_chart_labels,
        countries_doc_chart_data,
    )
    _build_country_chart(
        reproducibility_rows,
        "mean_fractional_reproducibility_score",
        countries_repro_chart_labels,
        countries_repro_chart_data,
    )

    countries_chart_row_count = max(
        len(countries_doc_chart_data), len(countries_repro_chart_data)
    )
    countries_chart_height = max(420, min(2200, countries_chart_row_count * 33))
    return render_template(
        "countries.html",
        countries_rows=countries_rows,
        countries_doc_chart_labels=countries_doc_chart_labels,
        countries_doc_chart_data=countries_doc_chart_data,
        countries_repro_chart_labels=countries_repro_chart_labels,
        countries_repro_chart_data=countries_repro_chart_data,
        countries_chart_height=countries_chart_height,
    )


@bp.route("/institutions/")
def institutions() -> str:
    documentation_rows = _store().list_institution_documentation_scores()
    reproducibility_rows = _store().list_institution_reproducibility_scores()
    institutions_rows: list[dict[str, object]] = []
    institutions_doc_chart_labels: list[str] = []
    institutions_doc_chart_data: list[dict[str, object]] = []
    institutions_repro_chart_labels: list[str] = []
    institutions_repro_chart_data: list[dict[str, object]] = []
    reproducibility_by_institution = {
        str(row.get("institution_normalized") or ""): row
        for row in reproducibility_rows
    }

    def _build_institution_chart(
        rows: list[dict[str, object]],
        mean_field_name: str,
        labels: list[str],
        data: list[dict[str, object]],
    ) -> None:
        for row in rows:
            mean_value = _to_float(row.get(mean_field_name))
            if mean_value is None:
                continue

            ci95_lower_value = _to_float(row.get("ci95_lower"))
            ci95_upper_value = _to_float(row.get("ci95_upper"))
            lower_bound = (
                ci95_lower_value if ci95_lower_value is not None else mean_value
            )
            upper_bound = (
                ci95_upper_value if ci95_upper_value is not None else mean_value
            )
            institution_name = _to_metric_display(row.get("institution_normalized"))

            labels.append(institution_name)
            data.append(
                {
                    "x": mean_value,
                    "xMin": lower_bound,
                    "xMax": upper_bound,
                    "institutionName": institution_name,
                }
            )

    for row in documentation_rows:
        institution = str(row.get("institution_normalized") or "")
        reproducibility_row = reproducibility_by_institution.get(institution, {})
        mean_repro_value = _to_float(
            reproducibility_row.get("mean_fractional_reproducibility_score")
        )
        mean_doc_value = _to_float(row.get("mean_fractional_documentation_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))
        mean_repro_sort = mean_repro_value if mean_repro_value is not None else -1.0
        mean_doc_sort = mean_doc_value if mean_doc_value is not None else -1.0

        institution_row = {
            "institution": _to_metric_display(row.get("institution_normalized")),
            "mean_fractional_reproducibility_score": _to_metric_display(
                reproducibility_row.get("mean_fractional_reproducibility_score")
            ),
            "mean_fractional_documentation_score": _to_metric_display(
                row.get("mean_fractional_documentation_score")
            ),
            "fractional_paper_count": _to_metric_display(
                row.get("fractional_paper_count")
            ),
            "contributing_papers": _to_metric_display(row.get("contributing_papers")),
            "mean_repro_sort": mean_repro_sort,
            "mean_doc_sort": mean_doc_sort,
            "fractional_paper_count_sort": (
                fractional_paper_count_value
                if fractional_paper_count_value is not None
                else -1.0
            ),
            "contributing_papers_sort": (
                contributing_papers_value
                if contributing_papers_value is not None
                else -1.0
            ),
        }
        institutions_rows.append(institution_row)

    _build_institution_chart(
        documentation_rows,
        "mean_fractional_documentation_score",
        institutions_doc_chart_labels,
        institutions_doc_chart_data,
    )
    _build_institution_chart(
        reproducibility_rows,
        "mean_fractional_reproducibility_score",
        institutions_repro_chart_labels,
        institutions_repro_chart_data,
    )

    institutions_chart_row_count = max(
        len(institutions_doc_chart_data), len(institutions_repro_chart_data)
    )
    institutions_chart_height = max(840, min(4400, institutions_chart_row_count * 66))
    return render_template(
        "institutions.html",
        institutions_rows=institutions_rows,
        institutions_doc_chart_labels=institutions_doc_chart_labels,
        institutions_doc_chart_data=institutions_doc_chart_data,
        institutions_repro_chart_labels=institutions_repro_chart_labels,
        institutions_repro_chart_data=institutions_repro_chart_data,
        institutions_chart_height=institutions_chart_height,
    )


@bp.route("/data/")
def data() -> str:
    total_papers = _store().get_total_papers_count()
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
    venue_stats_rows = _store().list_venue_stats()
    year_stats_rows = _store().list_year_stats()
    venue_stats_labels = [str(row.get("venue")) for row in venue_stats_rows]
    venue_stats_totals = [_to_int(row.get("total")) or 0 for row in venue_stats_rows]
    year_stats_labels = [str(row.get("year")) for row in year_stats_rows]
    year_stats_totals = [_to_int(row.get("total")) or 0 for row in year_stats_rows]
    return render_template(
        "data.html",
        total_papers=total_papers,
        data_chart_datasets=data_chart_datasets,
        data_rows=data_rows,
        venue_stats_labels=venue_stats_labels,
        venue_stats_totals=venue_stats_totals,
        year_stats_labels=year_stats_labels,
        year_stats_totals=year_stats_totals,
    )


@bp.route("/venues/<venue>")
def venue_years(venue: str) -> str:
    venue_row = _store().get_venue(venue)
    if venue_row is None:
        abort(404)

    editions = _store().list_editions(venue)
    percentage_metric_fields = [
        "percent_empirical_pseudocode",
        "percent_empirical_open_source_code",
        "percent_empirical_open_datasets",
        "percent_empirical_dataset_splits",
        "percent_empirical_hardware_specification",
        "percent_empirical_software_dependencies",
        "percent_empirical_experiment_setup",
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
            word.capitalize()
            for word in field.removeprefix("percent_empirical_").split("_")
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
        "reproducibility_score": _to_metric_display(
            reproducibility_scores.get("reproducibility_score")
        ),
        "documentation_global_mean": _to_metric_display(
            reproducibility_scores.get("documentation_global_mean")
        ),
        "documentation_global_median": _to_metric_display(
            reproducibility_scores.get("documentation_global_median")
        ),
        "documentation_other_mean": _to_metric_display(
            reproducibility_scores.get("documentation_other_mean")
        ),
        "documentation_dataset_mean": _to_metric_display(
            reproducibility_scores.get("documentation_dataset_mean")
        ),
        "documentation_code_mean": _to_metric_display(
            reproducibility_scores.get("documentation_code_mean")
        ),
        "percent_empirical": _to_percent_display(
            reproducibility_scores.get("percent_empirical")
        ),
        "percent_empirical_industry": _to_percent_display(
            reproducibility_scores.get("percent_empirical_industry")
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
