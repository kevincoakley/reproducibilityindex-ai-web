from __future__ import annotations

from flask import Blueprint

from app.page_routes import (
    about,
    data_page,
    home,
    methods,
    papers,
    rankings,
    seo,
    venues,
)


def register_routes(bp: Blueprint) -> None:
    home.register(bp)
    rankings.register(bp)
    methods.register(bp)
    about.register(bp)
    data_page.register(bp)
    venues.register(bp)
    papers.register(bp)
    seo.register(bp)
