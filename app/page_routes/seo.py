from __future__ import annotations

from flask import Blueprint, Response, current_app, render_template, url_for

from app.route_utils import _store

_CACHE_CONTROL = "public, max-age=86400"


def _site_url() -> str:
    """Return the configured public origin without a trailing slash."""
    return current_app.config["SITE_URL"].rstrip("/")


# Fixed content pages worth indexing. Detail pages (venues, editions, runs) are
# added dynamically from the datastore. Individual paper pages are intentionally
# excluded: there are ~80k of them and every page currently shares one <title>.
_STATIC_ENDPOINTS = (
    "pages.index",
    "pages.methods",
    "pages.about",
    "pages.data",
    "pages.countries",
    "pages.institutions",
)


def robots() -> Response:
    body = render_template("robots.txt", site_url=_site_url())
    return Response(
        body,
        mimetype="text/plain",
        headers={"Cache-Control": _CACHE_CONTROL},
    )


def sitemap() -> Response:
    base_url = _site_url()
    store = _store()

    paths = [url_for(endpoint) for endpoint in _STATIC_ENDPOINTS]
    paths += [
        url_for("pages.venue_years", venue=venue["venue"])
        for venue in store.list_venues()
    ]
    paths += [
        url_for("pages.venue_results", venue=edition["venue"], year=edition["year"])
        for edition in store.list_all_editions()
    ]
    paths += [url_for("pages.run_detail", run=run["run"]) for run in store.list_runs()]

    locs = [f"{base_url}{path}" for path in paths]
    body = render_template("sitemap.xml", locs=locs)
    return Response(
        body,
        mimetype="application/xml",
        headers={"Cache-Control": _CACHE_CONTROL},
    )


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/robots.txt", view_func=robots)
    bp.add_url_rule("/sitemap.xml", view_func=sitemap)
