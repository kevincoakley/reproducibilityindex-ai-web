from __future__ import annotations

from flask import Blueprint, abort, render_template

from app.route_utils import (
    RESULT_COLUMN_FIELDS,
    _store,
    _to_binary,
    _to_binary_icon,
    _to_float,
    _to_int,
    _to_metric_display,
    _to_percent_display,
)


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


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/venues/<venue>", view_func=venue_years)
    bp.add_url_rule("/venues/<venue>/<year>", view_func=venue_results)
