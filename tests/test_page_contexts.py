from __future__ import annotations

from app.viewmodels.page_contexts import (
    build_countries_context,
    build_data_context,
    build_home_context,
    build_institutions_context,
    build_paper_detail_context,
    build_venue_results_context,
)


def _make_edition_row(
    venue: str,
    year: str,
    *,
    acad_doc: object = None,
    acad_rep: object = None,
    ind_doc: object = None,
    ind_rep: object = None,
) -> dict:
    return {
        "venue": venue,
        "year": year,
        "number_papers": 10,
        "reproducibility_score": "0.5",
        "documentation_global_mean": "3.0",
        "documentation_global_median": "3.0",
        "documentation_other_mean": "1.5",
        "documentation_dataset_mean": "1.0",
        "documentation_code_mean": "0.5",
        "percent_empirical": "80",
        "percent_empirical_industry": "20",
        "academia_documentation_score": acad_doc,
        "academia_reproducibility_score": acad_rep,
        "industry_documentation_score": ind_doc,
        "industry_reproducibility_score": ind_rep,
        "url": f"https://example.org/{year}",
    }


def test_build_home_context_deduplicates_venues_and_sorts_chart_points() -> None:
    context = build_home_context(
        [
            _make_edition_row("ICML", "2024"),
            _make_edition_row("ICML", "2023"),
        ]
    )

    assert len(context["editions"]) == 1
    assert context["editions"][0]["venue"] == "ICML"
    repro_dataset = context["home_repro_score_chart_datasets"][0]
    assert repro_dataset["data"] == [{"x": 2023, "y": 0.5}, {"x": 2024, "y": 0.5}]


def test_build_home_context_builds_scatter_data_keyed_by_year() -> None:
    context = build_home_context(
        [
            _make_edition_row(
                "AAAI", "2025", acad_doc=3.87, acad_rep=0.56, ind_doc=3.73, ind_rep=0.50
            ),
            _make_edition_row(
                "ICLR", "2025", acad_doc=4.57, acad_rep=0.72, ind_doc=4.50, ind_rep=0.65
            ),
            _make_edition_row(
                "AAAI", "2024", acad_doc=3.50, acad_rep=0.52, ind_doc=3.40, ind_rep=0.45
            ),
        ]
    )

    scatter_data = context["home_scatter_data"]
    scatter_years = context["home_scatter_years"]

    assert scatter_years == ["2025", "2024"]
    assert len(scatter_data["2025"]["academia"]) == 2
    assert len(scatter_data["2025"]["industry"]) == 2
    assert len(scatter_data["2024"]["academia"]) == 1

    aaai_acad = next(
        p for p in scatter_data["2025"]["academia"] if p["venue"] == "AAAI"
    )
    assert aaai_acad["x"] == 3.87
    assert aaai_acad["y"] == 0.56
    assert aaai_acad["pointStyle"] == "star"

    iclr_ind = next(p for p in scatter_data["2025"]["industry"] if p["venue"] == "ICLR")
    assert iclr_ind["x"] == 4.50
    assert iclr_ind["pointStyle"] == "rectRot"


def test_build_home_context_omits_scatter_points_when_scores_missing() -> None:
    context = build_home_context(
        [
            _make_edition_row("AAAI", "2025", acad_doc=3.87, acad_rep=0.56),
            _make_edition_row("ICLR", "2025"),
        ]
    )

    scatter_data = context["home_scatter_data"]
    assert len(scatter_data["2025"]["academia"]) == 1
    assert scatter_data["2025"]["academia"][0]["venue"] == "AAAI"
    assert scatter_data["2025"]["industry"] == []


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


def test_build_institutions_context_uses_titles_for_display_labels() -> None:
    context = build_institutions_context(
        documentation_rows=[
            {
                "institution_normalized": "TU_Wien",
                "institution_title": "TU Wien",
                "mean_fractional_documentation_score": "0.8",
                "fractional_paper_count": "3.5",
                "contributing_papers": "4",
                "ci95_lower": "0.6",
                "ci95_upper": "0.9",
            }
        ],
        reproducibility_rows=[
            {
                "institution_normalized": "TU_Wien",
                "institution_title": "TU Wien",
                "mean_fractional_reproducibility_score": "0.7",
                "ci95_lower": None,
                "ci95_upper": None,
            }
        ],
    )

    assert context["institutions_rows"][0]["institution"] == "TU Wien"
    assert (
        context["institutions_rows"][0]["mean_fractional_reproducibility_score"]
        == "0.7"
    )
    assert context["institutions_doc_chart_labels"] == ["TU Wien"]
    assert context["institutions_doc_chart_data"][0]["institutionName"] == "TU Wien"
    assert context["institutions_repro_chart_labels"] == ["TU Wien"]


def test_build_institutions_context_scales_chart_height_from_100_plus_baseline() -> (
    None
):
    def institution_rows(row_count: int) -> list[dict[str, object]]:
        return [
            {
                "institution_normalized": f"Institution_{index}",
                "institution_title": f"Institution {index}",
                "mean_fractional_documentation_score": "0.8",
                "mean_fractional_reproducibility_score": "0.7",
                "fractional_paper_count": "3.5",
                "contributing_papers": "100",
                "ci95_lower": "0.6",
                "ci95_upper": "0.9",
            }
            for index in range(row_count)
        ]

    baseline_context = build_institutions_context(
        documentation_rows=institution_rows(251),
        reproducibility_rows=institution_rows(251),
    )
    larger_context = build_institutions_context(
        documentation_rows=institution_rows(502),
        reproducibility_rows=institution_rows(502),
    )
    smaller_context = build_institutions_context(
        documentation_rows=institution_rows(65),
        reproducibility_rows=institution_rows(65),
    )

    assert baseline_context["institutions_chart_height"] == 4400
    assert larger_context["institutions_chart_height"] == 8800
    assert smaller_context["institutions_chart_height"] == 1139


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
                "research_type_result": 0,
                "pseudocode_result": 1,
                "open_source_code_result": 0,
                "open_datasets_result": "1",
                "dataset_splits_result": None,
                "hardware_specification_result": "no",
                "software_dependencies_result": "yes",
                "experiment_setup_result": "unknown",
            },
            {
                "title": "Paper B",
                "research_type_result": 1,
                "pseudocode_result": 1,
                "open_source_code_result": 1,
                "open_datasets_result": 1,
                "dataset_splits_result": 1,
                "hardware_specification_result": 1,
                "software_dependencies_result": 1,
                "experiment_setup_result": 1,
            },
        ],
    )

    assert context["metrics"]["percent_empirical"] == "80%"
    result = context["results"][0]
    assert result["total"] == 3
    assert result["pseudocode_result_icon"] == "✅"
    assert result["open_source_code_result_icon"] == "❌"
    assert result["experiment_setup_result_icon"] == "N/A"
    assert len(context["results"]) == 2  # both papers appear in the table
    assert context["edition_bar_chart_labels"] == [
        "PC",
        "OSC",
        "ODS",
        "DS",
        "HS",
        "SD",
        "ES",
    ]
    # charts only count Paper A (empirical); Paper B (theoretical) is excluded
    assert context["edition_bar_chart_percentages"][0] == 100.0  # pseudocode True
    assert context["edition_bar_chart_percentages"][1] == 0.0  # open_source_code False
    assert context["edition_kde_histogram"] == {3: 1}
    assert context["edition_kde_max_total"] == 7


def test_build_data_and_paper_context_helpers() -> None:
    data_context = build_data_context(
        total_papers=42,
        total_input_tokens=1_000_000,
        total_output_tokens=500_000,
        paper_count_rows=[{"venue": "ICML", "year": "2024", "number_papers": "5"}],
        data_rows_source=[
            {
                "venue": "ICML",
                "year": "2024",
                "number_papers": "5",
                "run": "run-1",
                "url": "https://example.org",
                "input_tokens": 200000,
                "output_tokens": 80000,
            }
        ],
        venue_stats_rows=[{"venue": "ICML", "total": "5"}],
        year_stats_rows=[{"year": "2024", "total": "5"}],
    )
    assert data_context["venue_stats_totals"] == [5]
    assert data_context["data_chart_datasets"][0]["data"] == [{"x": 2024, "y": 5}]
    assert data_context["total_input_tokens"] == "1,000,000"
    assert data_context["total_output_tokens"] == "500,000"
    assert data_context["data_rows"][0]["input_tokens"] == "200,000"
    assert data_context["data_rows"][0]["output_tokens"] == "80,000"

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
            "input_tokens": 150000,
            "thoughts_tokens": 30000,
            "output_tokens": 20000,
        }
    )
    assert paper_context["detail_rows"][0]["verdict"] == "Theoretical"
    assert paper_context["detail_rows"][1]["verdict"] == "Industry"
    assert paper_context["input_tokens"] == "150,000"
    assert paper_context["output_tokens"] == "50,000"


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
