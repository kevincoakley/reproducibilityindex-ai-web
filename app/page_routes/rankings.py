from __future__ import annotations

from flask import Blueprint, render_template

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


def institutions() -> str:
    documentation_rows = _store().list_institution_documentation_scores()
    reproducibility_rows = _store().list_institution_reproducibility_scores()
    context = build_institutions_context(documentation_rows, reproducibility_rows)
    return render_template("institutions.html", **context)


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/countries/", view_func=countries)
    bp.add_url_rule("/institutions/", view_func=institutions)
