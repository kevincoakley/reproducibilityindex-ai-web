from __future__ import annotations

from flask import Blueprint, render_template

from app.route_utils import (
    _store,
    _to_float,
    _to_int,
    _to_metric_display,
    _to_percent_display,
)


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


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/", view_func=index)
