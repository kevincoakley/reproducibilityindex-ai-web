from __future__ import annotations

from app.viewmodels.page_contexts import (
    build_countries_context,
    build_data_context,
    build_home_context,
    build_paper_detail_context,
    build_venue_results_context,
)


def test_build_home_context_deduplicates_venues_and_sorts_chart_points() -> None:
    context = build_home_context(
        [
            {
                "venue": "ICML",
                "year": "2024",
                "number_papers": 10,
                "reproducibility_score": "0.2",
                "documentation_global_mean": "0.3",
                "documentation_global_median": "0.3",
                "documentation_other_mean": "0.3",
                "documentation_dataset_mean": "0.3",
                "documentation_code_mean": "0.3",
                "percent_empirical": "75",
                "percent_empirical_industry": "25",
                "url": "https://example.org/2024",
            },
            {
                "venue": "ICML",
                "year": "2023",
                "number_papers": 9,
                "reproducibility_score": "0.4",
                "documentation_global_mean": "0.5",
                "documentation_global_median": "0.5",
                "documentation_other_mean": "0.5",
                "documentation_dataset_mean": "0.5",
                "documentation_code_mean": "0.5",
                "percent_empirical": "70",
                "percent_empirical_industry": "20",
                "url": "https://example.org/2023",
            },
        ]
    )

    assert len(context["editions"]) == 1
    assert context["editions"][0]["venue"] == "ICML"
    repro_dataset = context["home_repro_score_chart_datasets"][0]
    assert repro_dataset["data"] == [{"x": 2023, "y": 0.4}, {"x": 2024, "y": 0.2}]


def test_build_countries_context_builds_chart_bounds_and_fallback_labels() -> None:
    context = build_countries_context(
        documentation_rows=[
            {
                "country": "US",
                "name": "United States",
                "flag": "",
                "mean_fractional_documentation_score": "0.8",
                "fractional_paper_count": "3.5",
                "contributing_papers": "4",
                "ci95_lower": "0.6",
                "ci95_upper": "0.9",
            }
        ],
        reproducibility_rows=[
            {
                "country": "US",
                "name": "United States",
                "flag": "",
                "mean_fractional_reproducibility_score": "0.7",
                "ci95_lower": None,
                "ci95_upper": None,
            }
        ],
    )

    assert (
        context["countries_rows"][0]["mean_fractional_reproducibility_score"] == "0.7"
    )
    assert context["countries_doc_chart_labels"] == ["United States"]
    assert context["countries_doc_chart_data"][0]["xMin"] == 0.6
    assert context["countries_repro_chart_data"][0]["xMin"] == 0.7
    assert context["countries_chart_height"] == 420


def test_build_venue_results_context_computes_totals_and_icons() -> None:
    context = build_venue_results_context(
        venue_row={"venue": "ICML"},
        year="2024",
        edition_url="https://example.org",
        reproducibility_scores={
            "number_papers": "10",
            "reproducibility_score": "0.9",
            "percent_empirical": "80",
            "percent_empirical_industry": "10",
        },
        raw_results=[
            {
                "title": "Paper A",
                "pseudocode_result": 1,
                "open_source_code_result": 0,
                "open_datasets_result": "1",
                "dataset_splits_result": None,
                "hardware_specification_result": "no",
                "software_dependencies_result": "yes",
                "experiment_setup_result": "unknown",
            }
        ],
    )

    assert context["metrics"]["percent_empirical"] == "80%"
    result = context["results"][0]
    assert result["total"] == 3
    assert result["pseudocode_result_icon"] == "✅"
    assert result["open_source_code_result_icon"] == "❌"
    assert result["experiment_setup_result_icon"] == "N/A"


def test_build_data_and_paper_context_helpers() -> None:
    data_context = build_data_context(
        total_papers=42,
        paper_count_rows=[{"venue": "ICML", "year": "2024", "number_papers": "5"}],
        data_rows_source=[
            {
                "venue": "ICML",
                "year": "2024",
                "number_papers": "5",
                "run": "run-1",
                "url": "https://example.org",
            }
        ],
        venue_stats_rows=[{"venue": "ICML", "total": "5"}],
        year_stats_rows=[{"year": "2024", "total": "5"}],
    )
    assert data_context["venue_stats_totals"] == [5]
    assert data_context["data_chart_datasets"][0]["data"] == [{"x": 2024, "y": 5}]

    paper_context = build_paper_detail_context(
        {
            "research_type_result": 1,
            "research_type_paper_text": "text",
            "affiliation_result": 2,
            "affiliation_paper_text": "text",
            "pseudocode_result": 0,
            "pseudocode_paper_text": "text",
            "open_source_code_result": 1,
            "open_source_code_paper_text": "text",
            "open_datasets_result": 1,
            "open_datasets_paper_text": "text",
            "dataset_splits_result": 1,
            "dataset_splits_paper_text": "text",
            "hardware_specification_result": 1,
            "hardware_specification_paper_text": "text",
            "software_dependencies_result": 1,
            "software_dependencies_paper_text": "text",
            "experiment_setup_result": 1,
            "experiment_setup_paper_text": "text",
        }
    )
    assert paper_context["detail_rows"][0]["verdict"] == "Theoretical"
    assert paper_context["detail_rows"][1]["verdict"] == "Industry"


def test_build_paper_detail_context_masks_email_addresses() -> None:
    paper_context = build_paper_detail_context(
        {
            "research_type_result": 0,
            "research_type_paper_text": (
                "Contact john.doe@example.org or {alice, bob, carol}@example.org for details."
            ),
            "affiliation_result": 0,
            "affiliation_paper_text": "",
            "pseudocode_result": 0,
            "pseudocode_paper_text": "",
            "open_source_code_result": 0,
            "open_source_code_paper_text": "",
            "open_datasets_result": 0,
            "open_datasets_paper_text": "",
            "dataset_splits_result": 0,
            "dataset_splits_paper_text": "",
            "hardware_specification_result": 0,
            "hardware_specification_paper_text": "",
            "software_dependencies_result": 0,
            "software_dependencies_paper_text": "",
            "experiment_setup_result": 0,
            "experiment_setup_paper_text": "",
        }
    )

    assert (
        paper_context["detail_rows"][0]["evidence"]
        == "Contact EMAIL or EMAIL for details."
    )
