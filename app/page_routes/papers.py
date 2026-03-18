from __future__ import annotations

from flask import Blueprint, abort, render_template

from app.route_utils import _store
from app.viewmodels.page_contexts import build_paper_detail_context


def _render_paper_detail(key: str) -> str:
    paper = _store().get_result(key)
    if paper is None:
        abort(404)

    context = build_paper_detail_context(paper)
    return render_template("paper_detail.html", **context)


def paper_detail_singular(key: str) -> str:
    return _render_paper_detail(key)


def paper_detail_plural(key: str) -> str:
    return _render_paper_detail(key)


def run_detail(run: str) -> str:
    run_row = _store().get_run(run)
    if run_row is None:
        abort(404)

    return render_template("run_detail.html", run_row=run_row)


def register(bp: Blueprint) -> None:
    bp.add_url_rule(
        "/paper/<key>", endpoint="paper_detail", view_func=paper_detail_singular
    )
    bp.add_url_rule(
        "/papers/<key>", endpoint="paper_detail_plural", view_func=paper_detail_plural
    )
    bp.add_url_rule("/runs/<run>", view_func=run_detail)
