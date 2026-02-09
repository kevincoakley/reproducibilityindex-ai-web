from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app
from app.routes import _to_verdict
from app.datastore.sqlite_store import SQLiteDataStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "results.sqlite"


@pytest.fixture(scope="session")
def sample_data() -> dict[str, str]:
    store = SQLiteDataStore(DB_PATH)

    for conference in store.list_conferences():
        conf = str(conference["conference"])
        for proceeding in store.list_proceedings(conf):
            year = str(proceeding["year"])
            results = store.list_results(conf, year)
            if results:
                first_result = results[0]
                return {
                    "conference": conf,
                    "year": year,
                    "paper_key": str(first_result["key"]),
                    "run": str(first_result["run"]),
                }

    raise RuntimeError("Could not find sample rows for tests")


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SITE_TITLE": "test.reproducibilityindex.ai",
            "SQLITE_DB_PATH": str(DB_PATH),
            "DB_BACKEND": "sqlite",
        }
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_conference_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/conferences/{sample_data['conference']}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert f"/conferences/{sample_data['conference']}/{sample_data['year']}" in body
    assert ">Number of Papers<" in body
    assert ">Global Mean<" in body
    assert ">Global Median<" in body
    assert ">Documentation Mean<" in body
    assert ">Dataset Mean<" in body
    assert ">Code Mean<" in body
    assert ">Percent Emperical<" in body
    assert ">Percent Industry<" in body


def test_conference_year_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(
        f"/conferences/{sample_data['conference']}/{sample_data['year']}"
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="paper-search"' in body
    assert "Conference Proceedings:" in body
    assert 'placeholder="Filter by title"' in body
    assert ">Authors<" not in body
    assert ">PC<" in body
    assert ">OSC<" in body
    assert ">ODS<" in body
    assert ">DS<" in body
    assert ">HS<" in body
    assert ">SD<" in body
    assert ">ES<" in body
    assert 'data-sort-key="total"' in body
    assert "Key: PC - Pseudocode" in body
    assert f"/papers/{sample_data['paper_key']}" in body
    assert ">Number of Papers<" in body
    assert ">Global Mean<" in body
    assert ">Global Median<" in body
    assert ">Documentation Mean<" in body
    assert ">Dataset Mean<" in body
    assert ">Code Mean<" in body
    assert ">Percent Emperical<" in body
    assert ">Percent Industry<" in body


def test_paper_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/paper/{sample_data['paper_key']}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert f"/runs/{sample_data['run']}" in body
    assert "Conference PDF" in body
    assert (
        "https://object.cloud.sdsc.edu/v1/AUTH_da4962d3368042ac8337e2dfdd3e7bf3/"
        f"ml-papers/{sample_data['conference']}/{sample_data['year']}/"
        f"{sample_data['paper_key']}.pdf"
    ) in body


def test_papers_alias_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/papers/{sample_data['paper_key']}")

    assert response.status_code == 200


def test_run_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/runs/{sample_data['run']}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "<pre><code>" in body


def test_dynamic_pages_404(client) -> None:
    assert client.get("/conferences/DOES_NOT_EXIST").status_code == 404
    assert client.get("/paper/does-not-exist").status_code == 404
    assert client.get("/runs/does-not-exist").status_code == 404


def test_research_type_mapping() -> None:
    assert _to_verdict(1, "research_type_result") == "Theoretical"
    assert _to_verdict(0, "research_type_result") == "Experimental"


def test_affiliation_mapping() -> None:
    assert _to_verdict(0, "affiliation_result") == "Academia"
    assert _to_verdict(1, "affiliation_result") == "Collaboration"
    assert _to_verdict(2, "affiliation_result") == "Industry"
