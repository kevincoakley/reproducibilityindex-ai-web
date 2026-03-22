from __future__ import annotations

from flask import Blueprint, render_template


def methods() -> str:
    return render_template("methods.html")


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/methods/", view_func=methods)
