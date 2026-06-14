from __future__ import annotations

from flask import Blueprint, render_template

from app.route_utils import _store
from app.viewmodels.page_contexts import build_data_context


def data() -> str:
    context = build_data_context(
        total_papers=_store().get_total_papers_count(),
        total_input_tokens=_store().get_total_input_tokens(),
        total_output_tokens=_store().get_total_output_tokens(),
        paper_count_rows=_store().list_paper_counts_by_venue_and_year(),
        data_rows_source=_store().list_data_rows(),
        venue_stats_rows=_store().list_venue_stats(),
        year_stats_rows=_store().list_year_stats(),
    )
    return render_template("data.html", **context)


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/data/", view_func=data)
