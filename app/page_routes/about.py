from __future__ import annotations

from flask import Blueprint, render_template


def about() -> str:
    return render_template("about.html")


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/about/", view_func=about)
