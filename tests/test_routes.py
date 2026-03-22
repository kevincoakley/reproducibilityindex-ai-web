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

    for venue in store.list_venues():
        venue_code = str(venue["venue"])
        for edition in store.list_editions(venue_code):
            year = str(edition["year"])
            results = store.list_results(venue_code, year)
            if results:
                first_result = results[0]
                return {
                    "venue": venue_code,
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
            "WEB_VERSION": "test-build",
            "SQLITE_DB_PATH": str(DB_PATH),
            "DB_BACKEND": "sqlite",
        }
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_home_page_lists_all_editions_table(
    client, sample_data: dict[str, str]
) -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="home-repro-score-chart"' in body
    assert 'id="home-global-mean-chart"' in body
    assert "cdn.jsdelivr.net/npm/chart.js" in body
    assert "const homeReproScoreChartDatasets =" in body
    assert "const homeDocMeanChartDatasets =" in body
    assert 'id="home-editions-table"' in body
    assert 'data-sort-key="docMean"' in body
    assert 'data-sort-key="reproScore"' in body
    assert 'aria-label="Reproducibility Score definition"' in body
    assert f"/venues/{sample_data['venue']}" in body
    assert ">Venue<" in body
    assert ">Year<" in body
    assert ">Papers<" in body
    assert ">Repro. Score<" in body
    assert ">Doc. Mean<" in body
    assert ">Doc. Median<" in body
    assert ">Dataset Doc.<" in body
    assert ">Code Doc.<" in body
    assert ">Other Doc.<" in body
    assert ">% Empirical<" in body
    assert ">% Industry<" in body
    expected_venue_count = len(SQLiteDataStore(DB_PATH).list_venues())
    assert body.count('data-venue="') == expected_venue_count
    assert 'id="site-version"' in body
    assert ">test-build<" in body


def test_footer_defaults_to_dev_when_web_version_env_var_unset(monkeypatch) -> None:
    monkeypatch.delenv("WEB_VERSION", raising=False)
    app = create_app(
        {
            "TESTING": True,
            "SITE_TITLE": "test.reproducibilityindex.ai",
            "SQLITE_DB_PATH": str(DB_PATH),
            "DB_BACKEND": "sqlite",
        }
    )
    test_client = app.test_client()

    response = test_client.get("/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="site-version"' in body
    assert ">dev<" in body


def test_countries_page_lists_chart_and_table(client) -> None:
    response = client.get("/countries/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="countries-repro-score-chart"' in body
    assert 'id="countries-doc-score-chart"' in body
    assert "chartjs-chart-error-bars" in body
    assert "const countriesReproChartData =" in body
    assert "const countriesDocChartData =" in body
    assert 'id="countries-table"' in body
    assert 'data-sort-key="meanFractionalReproducibilityScore"' in body
    assert ">Country<" in body
    assert ">Mean Fractional Reproducibility Score<" in body
    assert ">Mean Fractional Documentation Score<" in body
    assert ">Fractional Paper Count<" in body
    assert ">Contributing Papers<" in body
    expected_country_count = len(
        SQLiteDataStore(DB_PATH).list_country_documentation_scores()
    )
    assert (
        body.count('data-mean-fractional-reproducibility-score="')
        == expected_country_count
    )


def test_institutions_page_lists_chart_and_table(client) -> None:
    response = client.get("/institutions/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="institutions-repro-score-chart"' in body
    assert 'id="institutions-doc-score-chart"' in body
    assert "chartjs-chart-error-bars" in body
    assert "const institutionsReproChartData =" in body
    assert "const institutionsDocChartData =" in body
    assert 'id="institutions-table"' in body
    assert 'data-sort-key="meanFractionalReproducibilityScore"' in body
    assert ">Institution<" in body
    assert ">Mean Fractional Reproducibility Score<" in body
    assert ">Mean Fractional Documentation Score<" in body
    assert ">Fractional Paper Count<" in body
    assert ">Contributing Papers<" in body
    expected_institution_count = len(
        SQLiteDataStore(DB_PATH).list_institution_documentation_scores()
    )
    assert (
        body.count('data-mean-fractional-reproducibility-score="')
        == expected_institution_count
    )


def test_data_page_lists_stacked_area_chart(client) -> None:
    response = client.get("/data/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="data-papers-chart"' in body
    assert 'id="venue-total-pie-chart"' in body
    assert 'id="year-total-pie-chart"' in body
    assert "const dataChartDatasets =" in body
    assert "const venueStatsLabels =" in body
    assert "const yearStatsLabels =" in body
    assert 'stack: "papers"' in body
    assert 'type: "pie"' in body
    expected_total_papers = SQLiteDataStore(DB_PATH).get_total_papers_count()
    assert f"Total number of papers: {expected_total_papers}" in body
    assert "Number of papers by venue and edition year." in body
    assert ">Venue<" in body
    assert ">Year<" in body
    assert ">Number of Papers<" in body
    assert ">LLM Runs<" in body
    assert ">Website<" in body
    assert "/runs/" in body
    assert "sort-button" not in body


def test_methods_page(client) -> None:
    response = client.get("/methods/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="sec:documentation-reproducibility-score"' in body
    assert "mathjax@3/es5/tex-mml-chtml.js" in body
    assert "💡 Methods" in body


def test_venue_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/venues/{sample_data['venue']}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="venue-global-mean-chart"' in body
    assert "const venueChartDatasets =" in body
    assert (
        "The Percentage of Empirical Papers Documenting Each Reproducibility Variable"
        in body
    )
    assert f"/venues/{sample_data['venue']}/{sample_data['year']}" in body
    assert ">Venue<" in body
    assert ">Year<" in body
    assert ">Papers<" in body
    assert ">Repro. Score<" in body
    assert ">Doc. Mean<" in body
    assert ">Doc. Median<" in body
    assert ">Dataset Doc.<" in body
    assert ">Code Doc.<" in body
    assert ">Other Doc.<" in body
    assert ">% Empirical<" in body
    assert ">% Industry<" in body
    assert ">Website<" in body


def test_venue_year_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/venues/{sample_data['venue']}/{sample_data['year']}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'id="paper-search"' in body
    assert "Website:" in body
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
    assert "Key: PC - Pseudocode" not in body
    assert 'aria-label="PC definition"' in body
    assert 'aria-label="Reproducibility Score definition"' in body
    assert f"/papers/{sample_data['paper_key']}" in body
    assert ">Venue<" in body
    assert ">Year<" in body
    assert ">Papers<" in body
    assert ">Repro. Score<" in body
    assert ">Doc. Mean<" in body
    assert ">Doc. Median<" in body
    assert ">Dataset Doc.<" in body
    assert ">Code Doc.<" in body
    assert ">Other Doc.<" in body
    assert ">% Empirical<" in body
    assert ">% Industry<" in body
    assert ">Website<" in body


def test_paper_page(client, sample_data: dict[str, str]) -> None:
    response = client.get(f"/paper/{sample_data['paper_key']}")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert f"/runs/{sample_data['run']}" in body
    assert "Venue PDF" in body
    assert (
        "https://object.cloud.sdsc.edu/v1/AUTH_da4962d3368042ac8337e2dfdd3e7bf3/"
        f"ml-papers/{sample_data['venue']}/{sample_data['year']}/"
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
    assert client.get("/venues/DOES_NOT_EXIST").status_code == 404
    assert client.get("/paper/does-not-exist").status_code == 404
    assert client.get("/runs/does-not-exist").status_code == 404


def test_research_type_mapping() -> None:
    assert _to_verdict(1, "research_type_result") == "Theoretical"
    assert _to_verdict(0, "research_type_result") == "Experimental"


def test_affiliation_mapping() -> None:
    assert _to_verdict(0, "affiliation_result") == "Academia"
    assert _to_verdict(1, "affiliation_result") == "Collaboration"
    assert _to_verdict(2, "affiliation_result") == "Industry"
