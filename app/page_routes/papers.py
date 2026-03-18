from __future__ import annotations

from flask import Blueprint, abort, render_template

from app.route_utils import DETAIL_ROWS, _store, _to_verdict


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
