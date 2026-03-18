from __future__ import annotations

from flask import Blueprint, render_template

from app.route_utils import _store, _to_int, _to_metric_display


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


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/data/", view_func=data)
