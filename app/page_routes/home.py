from __future__ import annotations

from flask import Blueprint, render_template

from app.route_utils import _store
from app.viewmodels.page_contexts import build_home_context


def index() -> str:
    context = build_home_context(_store().list_all_editions())
    return render_template("home.html", **context)


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/", view_func=index)
