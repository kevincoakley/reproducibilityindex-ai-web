from __future__ import annotations

from flask import Blueprint, abort, render_template

from app.route_utils import _store
from app.viewmodels.page_contexts import (
    build_venue_results_context,
    build_venue_years_context,
)


def venue_years(venue: str) -> str:
    venue_row = _store().get_venue(venue)
    if venue_row is None:
        abort(404)

    editions = _store().list_editions(venue)
    context = build_venue_years_context(venue_row, editions)
    return render_template("venue_years.html", **context)


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
    context = build_venue_results_context(
        venue_row=venue_row,
        year=year,
        edition_url=edition_url,
        reproducibility_scores=(
            _store().get_edition_reproducibility_scores(venue, year) or {}
        ),
        raw_results=_store().list_results(venue, year),
    )
    return render_template("venue_results.html", **context)


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/venues/<venue>", view_func=venue_years)
    bp.add_url_rule("/venues/<venue>/<year>", view_func=venue_results)
