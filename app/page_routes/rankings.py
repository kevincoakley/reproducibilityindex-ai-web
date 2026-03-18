from __future__ import annotations

from flask import Blueprint, render_template

from app.route_utils import _store, _to_float, _to_metric_display


def countries() -> str:
    documentation_rows = _store().list_country_documentation_scores()
    reproducibility_rows = _store().list_country_reproducibility_scores()
    countries_rows: list[dict[str, object]] = []
    countries_doc_chart_labels: list[str] = []
    countries_doc_chart_data: list[dict[str, object]] = []
    countries_repro_chart_labels: list[str] = []
    countries_repro_chart_data: list[dict[str, object]] = []
    reproducibility_by_country = {
        str(row.get("country") or ""): row for row in reproducibility_rows
    }

    def _build_country_chart(
        rows: list[dict[str, object]],
        mean_field_name: str,
        labels: list[str],
        data: list[dict[str, object]],
    ) -> None:
        for row in rows:
            mean_value = _to_float(row.get(mean_field_name))
            if mean_value is None:
                continue

            ci95_lower_value = _to_float(row.get("ci95_lower"))
            ci95_upper_value = _to_float(row.get("ci95_upper"))
            lower_bound = (
                ci95_lower_value if ci95_lower_value is not None else mean_value
            )
            upper_bound = (
                ci95_upper_value if ci95_upper_value is not None else mean_value
            )
            flag = str(row.get("flag") or "").strip()
            country_name = _to_metric_display(row.get("name"))

            labels.append(flag if flag else country_name)
            data.append(
                {
                    "x": mean_value,
                    "xMin": lower_bound,
                    "xMax": upper_bound,
                    "countryName": country_name,
                }
            )

    for row in documentation_rows:
        country_code = str(row.get("country") or "")
        reproducibility_row = reproducibility_by_country.get(country_code, {})
        mean_repro_value = _to_float(
            reproducibility_row.get("mean_fractional_reproducibility_score")
        )
        mean_doc_value = _to_float(row.get("mean_fractional_documentation_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))
        mean_repro_sort = mean_repro_value if mean_repro_value is not None else -1.0
        mean_doc_sort = mean_doc_value if mean_doc_value is not None else -1.0
        flag = str(row.get("flag") or "").strip()

        country_row = {
            "name": _to_metric_display(row.get("name")),
            "country": _to_metric_display(country_code),
            "flag": flag if flag else "N/A",
            "mean_fractional_reproducibility_score": _to_metric_display(
                reproducibility_row.get("mean_fractional_reproducibility_score")
            ),
            "mean_fractional_documentation_score": _to_metric_display(
                row.get("mean_fractional_documentation_score")
            ),
            "fractional_paper_count": _to_metric_display(
                row.get("fractional_paper_count")
            ),
            "contributing_papers": _to_metric_display(row.get("contributing_papers")),
            "mean_repro_sort": mean_repro_sort,
            "mean_doc_sort": mean_doc_sort,
            "fractional_paper_count_sort": (
                fractional_paper_count_value
                if fractional_paper_count_value is not None
                else -1.0
            ),
            "contributing_papers_sort": (
                contributing_papers_value
                if contributing_papers_value is not None
                else -1.0
            ),
        }
        countries_rows.append(country_row)

    _build_country_chart(
        documentation_rows,
        "mean_fractional_documentation_score",
        countries_doc_chart_labels,
        countries_doc_chart_data,
    )
    _build_country_chart(
        reproducibility_rows,
        "mean_fractional_reproducibility_score",
        countries_repro_chart_labels,
        countries_repro_chart_data,
    )

    countries_chart_row_count = max(
        len(countries_doc_chart_data), len(countries_repro_chart_data)
    )
    countries_chart_height = max(420, min(2200, countries_chart_row_count * 33))
    return render_template(
        "countries.html",
        countries_rows=countries_rows,
        countries_doc_chart_labels=countries_doc_chart_labels,
        countries_doc_chart_data=countries_doc_chart_data,
        countries_repro_chart_labels=countries_repro_chart_labels,
        countries_repro_chart_data=countries_repro_chart_data,
        countries_chart_height=countries_chart_height,
    )


def institutions() -> str:
    documentation_rows = _store().list_institution_documentation_scores()
    reproducibility_rows = _store().list_institution_reproducibility_scores()
    institutions_rows: list[dict[str, object]] = []
    institutions_doc_chart_labels: list[str] = []
    institutions_doc_chart_data: list[dict[str, object]] = []
    institutions_repro_chart_labels: list[str] = []
    institutions_repro_chart_data: list[dict[str, object]] = []
    reproducibility_by_institution = {
        str(row.get("institution_normalized") or ""): row
        for row in reproducibility_rows
    }

    def _build_institution_chart(
        rows: list[dict[str, object]],
        mean_field_name: str,
        labels: list[str],
        data: list[dict[str, object]],
    ) -> None:
        for row in rows:
            mean_value = _to_float(row.get(mean_field_name))
            if mean_value is None:
                continue

            ci95_lower_value = _to_float(row.get("ci95_lower"))
            ci95_upper_value = _to_float(row.get("ci95_upper"))
            lower_bound = (
                ci95_lower_value if ci95_lower_value is not None else mean_value
            )
            upper_bound = (
                ci95_upper_value if ci95_upper_value is not None else mean_value
            )
            institution_name = _to_metric_display(row.get("institution_normalized"))

            labels.append(institution_name)
            data.append(
                {
                    "x": mean_value,
                    "xMin": lower_bound,
                    "xMax": upper_bound,
                    "institutionName": institution_name,
                }
            )

    for row in documentation_rows:
        institution = str(row.get("institution_normalized") or "")
        reproducibility_row = reproducibility_by_institution.get(institution, {})
        mean_repro_value = _to_float(
            reproducibility_row.get("mean_fractional_reproducibility_score")
        )
        mean_doc_value = _to_float(row.get("mean_fractional_documentation_score"))
        fractional_paper_count_value = _to_float(row.get("fractional_paper_count"))
        contributing_papers_value = _to_float(row.get("contributing_papers"))
        mean_repro_sort = mean_repro_value if mean_repro_value is not None else -1.0
        mean_doc_sort = mean_doc_value if mean_doc_value is not None else -1.0

        institution_row = {
            "institution": _to_metric_display(row.get("institution_normalized")),
            "mean_fractional_reproducibility_score": _to_metric_display(
                reproducibility_row.get("mean_fractional_reproducibility_score")
            ),
            "mean_fractional_documentation_score": _to_metric_display(
                row.get("mean_fractional_documentation_score")
            ),
            "fractional_paper_count": _to_metric_display(
                row.get("fractional_paper_count")
            ),
            "contributing_papers": _to_metric_display(row.get("contributing_papers")),
            "mean_repro_sort": mean_repro_sort,
            "mean_doc_sort": mean_doc_sort,
            "fractional_paper_count_sort": (
                fractional_paper_count_value
                if fractional_paper_count_value is not None
                else -1.0
            ),
            "contributing_papers_sort": (
                contributing_papers_value
                if contributing_papers_value is not None
                else -1.0
            ),
        }
        institutions_rows.append(institution_row)

    _build_institution_chart(
        documentation_rows,
        "mean_fractional_documentation_score",
        institutions_doc_chart_labels,
        institutions_doc_chart_data,
    )
    _build_institution_chart(
        reproducibility_rows,
        "mean_fractional_reproducibility_score",
        institutions_repro_chart_labels,
        institutions_repro_chart_data,
    )

    institutions_chart_row_count = max(
        len(institutions_doc_chart_data), len(institutions_repro_chart_data)
    )
    institutions_chart_height = max(840, min(4400, institutions_chart_row_count * 66))
    return render_template(
        "institutions.html",
        institutions_rows=institutions_rows,
        institutions_doc_chart_labels=institutions_doc_chart_labels,
        institutions_doc_chart_data=institutions_doc_chart_data,
        institutions_repro_chart_labels=institutions_repro_chart_labels,
        institutions_repro_chart_data=institutions_repro_chart_data,
        institutions_chart_height=institutions_chart_height,
    )


def register(bp: Blueprint) -> None:
    bp.add_url_rule("/countries/", view_func=countries)
    bp.add_url_rule("/institutions/", view_func=institutions)
