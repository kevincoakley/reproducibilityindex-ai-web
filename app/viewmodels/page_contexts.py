from __future__ import annotations

import re

from app.route_utils import (
    DETAIL_ROWS,
    RESULT_COLUMN_FIELD_LABELS,
    RESULT_COLUMN_FIELDS,
    _to_binary,
    _to_binary_icon,
    _to_float,
    _to_int,
    _to_metric_display,
    _to_percent_display,
    _to_verdict,
)

Record = dict[str, object]

INSTITUTION_CHART_BASELINE_ROW_COUNT = 251
INSTITUTION_CHART_BASELINE_HEIGHT = 4400
INSTITUTION_CHART_MIN_HEIGHT = 840

GROUPED_EMAIL_PATTERN = re.compile(
    r"\{[^{}\r\n]+(?:\s*,\s*[^{}\r\n]+)+\}@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}"
)
STANDARD_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b"
)


def _mask_email_addresses(text: str) -> str:
    masked = GROUPED_EMAIL_PATTERN.sub("EMAIL", text)
    return STANDARD_EMAIL_PATTERN.sub("EMAIL", masked)


_VENUE_POINT_STYLES: dict[str, str] = {
    "AAAI": "star",
    "DMLR": "triangle",
    "ICLR": "rectRot",
    "ICML": "rect",
    "IJCAI": "circle",
    "JAIR": "cross",
    "JMLR": "crossRot",
    "NeurIPS": "rectRounded",
    "TMLR": "dash",
}


def build_home_context(all_edition_source_rows: list[Record]) -> dict[str, object]:
    all_edition_rows: list[Record] = []
    doc_mean_chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    repro_score_chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    scatter_by_year: dict[str, dict[str, list[dict]]] = {}

    for row in all_edition_source_rows:
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

        if venue and year_value is not None:
            acad_doc = _to_float(row.get("academia_documentation_score"))
            acad_rep = _to_float(row.get("academia_reproducibility_score"))
            ind_doc = _to_float(row.get("industry_documentation_score"))
            ind_rep = _to_float(row.get("industry_reproducibility_score"))
            point_style = _VENUE_POINT_STYLES.get(venue, "circle")
            year_key = str(year_value)
            scatter_by_year.setdefault(year_key, {"academia": [], "industry": []})
            if acad_doc is not None and acad_rep is not None:
                scatter_by_year[year_key]["academia"].append(
                    {
                        "x": acad_doc,
                        "y": acad_rep,
                        "venue": venue,
                        "pointStyle": point_style,
                    }
                )
            if ind_doc is not None and ind_rep is not None:
                scatter_by_year[year_key]["industry"].append(
                    {
                        "x": ind_doc,
                        "y": ind_rep,
                        "venue": venue,
                        "pointStyle": point_style,
                    }
                )

    editions: list[Record] = []
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

    home_scatter_years = sorted(scatter_by_year.keys(), reverse=True)
    home_scatter_data = {y: scatter_by_year[y] for y in home_scatter_years}
    home_scatter_venue_shapes = [
        {"venue": v, "pointStyle": s} for v, s in _VENUE_POINT_STYLES.items()
    ]

    return {
        "editions": editions,
        "home_doc_mean_chart_datasets": home_doc_mean_chart_datasets,
        "home_repro_score_chart_datasets": home_repro_score_chart_datasets,
        "home_scatter_data": home_scatter_data,
        "home_scatter_years": home_scatter_years,
        "home_scatter_venue_shapes": home_scatter_venue_shapes,
    }


def _build_ci_chart_data(
    rows: list[Record],
    mean_field_name: str,
    name_key: str,
    chart_name_key: str,
    use_flag_as_label: bool,
) -> tuple[list[str], list[Record]]:
    labels: list[str] = []
    data: list[Record] = []
    for row in rows:
        mean_value = _to_float(row.get(mean_field_name))
        if mean_value is None:
            continue

        ci95_lower_value = _to_float(row.get("ci95_lower"))
        ci95_upper_value = _to_float(row.get("ci95_upper"))
        lower_bound = ci95_lower_value if ci95_lower_value is not None else mean_value
        upper_bound = ci95_upper_value if ci95_upper_value is not None else mean_value
        name_value = _to_metric_display(row.get(name_key))
        if use_flag_as_label:
            flag = str(row.get("flag") or "").strip()
            labels.append(flag if flag else name_value)
        else:
            labels.append(name_value)

        data.append(
            {
                "x": mean_value,
                "xMin": lower_bound,
                "xMax": upper_bound,
                chart_name_key: name_value,
            }
        )

    return labels, data


def build_countries_context(
    documentation_rows: list[Record], reproducibility_rows: list[Record]
) -> dict[str, object]:
    countries_rows: list[Record] = []
    reproducibility_by_country = {
        str(row.get("country") or ""): row for row in reproducibility_rows
    }

    for row in documentation_rows:
        country_code = str(row.get("country") or "")
        reproducibility_row = reproducibility_by_country.get(country_code, {})
        mean_repro_value = _to_float(
            reproducibility_row.get("mean_fractional_reproducibility_score")
        )
        mean_doc_value = _to_float(row.get("mean_fractional_documentation_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))
        flag = str(row.get("flag") or "").strip()

        countries_rows.append(
            {
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
                "contributing_papers": _to_metric_display(
                    row.get("contributing_papers")
                ),
                "mean_repro_sort": (
                    mean_repro_value if mean_repro_value is not None else -1.0
                ),
                "mean_doc_sort": mean_doc_value if mean_doc_value is not None else -1.0,
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
        )

    countries_doc_chart_labels, countries_doc_chart_data = _build_ci_chart_data(
        documentation_rows,
        "mean_fractional_documentation_score",
        "name",
        "countryName",
        True,
    )
    countries_repro_chart_labels, countries_repro_chart_data = _build_ci_chart_data(
        reproducibility_rows,
        "mean_fractional_reproducibility_score",
        "name",
        "countryName",
        True,
    )

    countries_chart_row_count = max(
        len(countries_doc_chart_data), len(countries_repro_chart_data)
    )
    countries_chart_height = max(420, min(2200, countries_chart_row_count * 33))

    return {
        "countries_rows": countries_rows,
        "countries_doc_chart_labels": countries_doc_chart_labels,
        "countries_doc_chart_data": countries_doc_chart_data,
        "countries_repro_chart_labels": countries_repro_chart_labels,
        "countries_repro_chart_data": countries_repro_chart_data,
        "countries_chart_height": countries_chart_height,
    }


def build_institutions_context(
    documentation_rows: list[Record], reproducibility_rows: list[Record]
) -> dict[str, object]:
    institutions_rows: list[Record] = []
    reproducibility_by_institution = {
        str(row.get("institution_normalized") or ""): row
        for row in reproducibility_rows
    }

    for row in documentation_rows:
        institution = str(row.get("institution_normalized") or "")
        reproducibility_row = reproducibility_by_institution.get(institution, {})
        institution_title = row.get("institution_title") or institution
        mean_repro_value = _to_float(
            reproducibility_row.get("mean_fractional_reproducibility_score")
        )
        mean_doc_value = _to_float(row.get("mean_fractional_documentation_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))

        institutions_rows.append(
            {
                "institution": _to_metric_display(institution_title),
                "mean_fractional_reproducibility_score": _to_metric_display(
                    reproducibility_row.get("mean_fractional_reproducibility_score")
                ),
                "mean_fractional_documentation_score": _to_metric_display(
                    row.get("mean_fractional_documentation_score")
                ),
                "fractional_paper_count": _to_metric_display(
                    row.get("fractional_paper_count")
                ),
                "contributing_papers": _to_metric_display(
                    row.get("contributing_papers")
                ),
                "mean_repro_sort": (
                    mean_repro_value if mean_repro_value is not None else -1.0
                ),
                "mean_doc_sort": mean_doc_value if mean_doc_value is not None else -1.0,
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
        )

    institutions_doc_chart_labels, institutions_doc_chart_data = _build_ci_chart_data(
        documentation_rows,
        "mean_fractional_documentation_score",
        "institution_title",
        "institutionName",
        False,
    )
    institutions_repro_chart_labels, institutions_repro_chart_data = (
        _build_ci_chart_data(
            reproducibility_rows,
            "mean_fractional_reproducibility_score",
            "institution_title",
            "institutionName",
            False,
        )
    )

    institutions_chart_row_count = max(
        len(institutions_doc_chart_data), len(institutions_repro_chart_data)
    )
    institutions_chart_height = max(
        INSTITUTION_CHART_MIN_HEIGHT,
        round(
            institutions_chart_row_count
            * INSTITUTION_CHART_BASELINE_HEIGHT
            / INSTITUTION_CHART_BASELINE_ROW_COUNT
        ),
    )

    return {
        "institutions_rows": institutions_rows,
        "institutions_doc_chart_labels": institutions_doc_chart_labels,
        "institutions_doc_chart_data": institutions_doc_chart_data,
        "institutions_repro_chart_labels": institutions_repro_chart_labels,
        "institutions_repro_chart_data": institutions_repro_chart_data,
        "institutions_chart_height": institutions_chart_height,
    }


def build_data_context(
    total_papers: int,
    paper_count_rows: list[Record],
    data_rows_source: list[Record],
    venue_stats_rows: list[Record],
    year_stats_rows: list[Record],
) -> dict[str, object]:
    chart_points_by_venue: dict[str, list[dict[str, float]]] = {}
    for row in paper_count_rows:
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
        for row in data_rows_source
    ]

    return {
        "total_papers": total_papers,
        "data_chart_datasets": data_chart_datasets,
        "data_rows": data_rows,
        "venue_stats_labels": [str(row.get("venue")) for row in venue_stats_rows],
        "venue_stats_totals": [
            _to_int(row.get("total")) or 0 for row in venue_stats_rows
        ],
        "year_stats_labels": [str(row.get("year")) for row in year_stats_rows],
        "year_stats_totals": [
            _to_int(row.get("total")) or 0 for row in year_stats_rows
        ],
    }


def build_venue_years_context(
    venue_row: Record, editions: list[Record]
) -> dict[str, object]:
    percentage_metric_fields = [
        "percent_empirical_pseudocode",
        "percent_empirical_open_source_code",
        "percent_empirical_open_datasets",
        "percent_empirical_dataset_splits",
        "percent_empirical_hardware_specification",
        "percent_empirical_software_dependencies",
        "percent_empirical_experiment_setup",
    ]
    venue_chart_datasets: list[Record] = []
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

    return {
        "venue": venue_row,
        "editions": editions,
        "venue_chart_datasets": venue_chart_datasets,
    }


def build_venue_results_context(
    venue_row: Record,
    year: str,
    edition_url: str,
    reproducibility_scores: Record,
    raw_results: list[Record],
) -> dict[str, object]:
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

    metric_true_counts: dict[str, int] = {field: 0 for field in RESULT_COLUMN_FIELDS}
    score_histogram: dict[int, int] = {}
    results: list[Record] = []
    for row in raw_results:
        normalized = dict(row)
        total = 0
        is_empirical = _to_binary(row.get("research_type_result")) == 0
        for field in RESULT_COLUMN_FIELDS:
            binary_value = _to_binary(row.get(field))
            if binary_value is not None:
                total += binary_value
                if is_empirical:
                    metric_true_counts[field] += binary_value
            normalized[f"{field}_binary"] = (
                binary_value if binary_value is not None else -1
            )
            normalized[f"{field}_icon"] = _to_binary_icon(row.get(field))
        normalized["total"] = total
        if is_empirical:
            score_histogram[total] = score_histogram.get(total, 0) + 1
        results.append(normalized)

    total_papers = sum(score_histogram.values())
    if total_papers > 0:
        edition_bar_chart_percentages: list[float] = [
            round(metric_true_counts[field] / total_papers * 100, 1)
            for field, _ in RESULT_COLUMN_FIELD_LABELS
        ]
    else:
        edition_bar_chart_percentages = [0.0] * len(RESULT_COLUMN_FIELD_LABELS)

    return {
        "venue": venue_row,
        "year": year,
        "edition_url": edition_url,
        "metrics": metrics,
        "results": results,
        "edition_bar_chart_labels": [label for _, label in RESULT_COLUMN_FIELD_LABELS],
        "edition_bar_chart_percentages": edition_bar_chart_percentages,
        "edition_kde_histogram": score_histogram,
        "edition_kde_max_total": len(RESULT_COLUMN_FIELD_LABELS),
    }


def build_paper_detail_context(paper: Record) -> dict[str, object]:
    detail_rows: list[dict[str, str]] = []
    for label, verdict_field, text_field in DETAIL_ROWS:
        evidence = _mask_email_addresses(str(paper.get(text_field) or ""))
        detail_rows.append(
            {
                "label": label,
                "verdict": _to_verdict(paper.get(verdict_field), verdict_field),
                "evidence": evidence,
            }
        )

    return {
        "paper": paper,
        "detail_rows": detail_rows,
    }
