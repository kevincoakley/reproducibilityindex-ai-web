from __future__ import annotations

from flask import Blueprint, abort, render_template

from app.route_utils import _store
from app.viewmodels.page_contexts import (
    build_countries_context,
    build_institutions_context,
)


def countries() -> str:
    documentation_rows = _store().list_country_documentation_scores()
    reproducibility_rows = _store().list_country_reproducibility_scores()
    context = build_countries_context(documentation_rows, reproducibility_rows)
    return render_template("countries.html", **context)


INSTITUTION_CONTRIBUTING_PAPERS_THRESHOLDS = (25, 100, 500, 1000)
DEFAULT_INSTITUTION_CONTRIBUTING_PAPERS = 100


def institutions(
    min_contributing_papers: int = DEFAULT_INSTITUTION_CONTRIBUTING_PAPERS,
) -> str:
    if min_contributing_papers not in INSTITUTION_CONTRIBUTING_PAPERS_THRESHOLDS:
        abort(404)

    documentation_rows = _store().list_institution_documentation_scores(
        min_contributing_papers=min_contributing_papers
    )
    reproducibility_rows = _store().list_institution_reproducibility_scores(
        min_contributing_papers=min_contributing_papers
    )
    context = build_institutions_context(documentation_rows, reproducibility_rows)
    context.update(
        {
            "institution_contributing_papers_thresholds": (
                INSTITUTION_CONTRIBUTING_PAPERS_THRESHOLDS
            ),
            "selected_institution_contributing_papers": min_contributing_papers,
        }
    )
    return render_template("institutions.html", **context)


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/countries/", view_func=countries)
    bp.add_url_rule("/institutions/", view_func=institutions)
    bp.add_url_rule(
        "/institutions/contributing_papers/<int:min_contributing_papers>",
        view_func=institutions,
    )
