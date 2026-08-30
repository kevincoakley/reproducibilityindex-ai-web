from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app import create_app
from app.datastore.sqlite_store import SQLiteDataStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "results.sqlite"
SITE_URL = "https://test.example"
CACHE_CONTROL = "public, max-age=86400"

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
_STATIC_PAGE_COUNT = 6  # /, /methods/, /about/, /data/, /countries/, /institutions/


@pytest.fixture()
def app():
    return create_app(
        {
            "TESTING": True,
            "SITE_TITLE": "test.reproducibilityindex.ai",
            "SITE_URL": SITE_URL,
            "SQLITE_DB_PATH": str(DB_PATH),
            "DB_BACKEND": "sqlite",
        }
    )


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def store() -> SQLiteDataStore:
    return SQLiteDataStore(DB_PATH)


def test_robots_txt_is_open_and_points_at_sitemap(client) -> None:
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert response.headers["Cache-Control"] == CACHE_CONTROL

    body = response.get_data(as_text=True)
    assert "User-agent: *" in body
    assert "Allow: /" in body
    assert "Disallow:" not in body
    assert f"Sitemap: {SITE_URL}/sitemap.xml" in body


def test_sitemap_is_valid_xml_with_absolute_https_locs(client, store) -> None:
    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    assert response.headers["Cache-Control"] == CACHE_CONTROL

    root = ET.fromstring(response.get_data())
    locs = [el.text for el in root.findall(".//sm:loc", _SITEMAP_NS)]

    assert locs, "sitemap has no <loc> entries"
    assert all(loc.startswith(f"{SITE_URL}/") for loc in locs)

    expected_count = (
        _STATIC_PAGE_COUNT
        + len(store.list_venues())
        + len(store.list_all_editions())
        + len(store.list_runs())
    )
    assert len(locs) == expected_count


def test_sitemap_lists_content_and_detail_pages(client, store) -> None:
    body = client.get("/sitemap.xml").get_data(as_text=True)

    assert f"<loc>{SITE_URL}/</loc>" in body
    assert f"<loc>{SITE_URL}/methods/</loc>" in body
    assert f"<loc>{SITE_URL}/institutions/</loc>" in body

    venue = str(store.list_venues()[0]["venue"])
    assert f"<loc>{SITE_URL}/venues/{venue}</loc>" in body

    edition = store.list_all_editions()[0]
    assert f"<loc>{SITE_URL}/venues/{edition['venue']}/{edition['year']}</loc>" in body

    run = str(store.list_runs()[0]["run"])
    assert f"<loc>{SITE_URL}/runs/{run}</loc>" in body


def test_sitemap_excludes_paper_and_threshold_pages(client) -> None:
    body = client.get("/sitemap.xml").get_data(as_text=True)

    assert "/paper/" not in body
    assert "/papers/" not in body
    assert "/contributing_papers/" not in body


def test_trailing_slash_in_site_url_does_not_produce_double_slashes() -> None:
    app = create_app(
        {
            "TESTING": True,
            "SITE_TITLE": "test.reproducibilityindex.ai",
            "SITE_URL": f"{SITE_URL}/",
            "SQLITE_DB_PATH": str(DB_PATH),
            "DB_BACKEND": "sqlite",
        }
    )
    client = app.test_client()

    robots_body = client.get("/robots.txt").get_data(as_text=True)
    assert f"Sitemap: {SITE_URL}/sitemap.xml" in robots_body

    root = ET.fromstring(client.get("/sitemap.xml").get_data())
    locs = [el.text for el in root.findall(".//sm:loc", _SITEMAP_NS)]
    assert locs
    assert all(loc.startswith(f"{SITE_URL}/") for loc in locs)
    assert all("//" not in loc[len("https://") :] for loc in locs)
