from __future__ import annotations

from flask import Flask

from app.route_utils import (
    _store,
    _to_binary,
    _to_binary_icon,
    _to_float,
    _to_int,
    _to_metric_display,
    _to_percent_display,
    _to_verdict,
)


def test_to_verdict_handles_special_and_general_cases() -> None:
    assert _to_verdict(1, "research_type_result") == "Theoretical"
    assert _to_verdict(0, "research_type_result") == "Experimental"
    assert _to_verdict(2, "affiliation_result") == "Industry"
    assert _to_verdict(True) == "Yes"
    assert _to_verdict(" no ") == "No"
    assert _to_verdict(None) == "N/A"
    assert _to_verdict("Custom") == "Custom"


def test_to_binary_and_icons_handle_known_and_unknown_values() -> None:
    assert _to_binary(True) == 1
    assert _to_binary("0") == 0
    assert _to_binary("yes") == 1
    assert _to_binary("unknown") is None

    assert _to_binary_icon(1) == "✅"
    assert _to_binary_icon("0") == "❌"
    assert _to_binary_icon("unknown") == "N/A"


def test_metric_percent_float_and_int_coercion() -> None:
    assert _to_metric_display(None) == "N/A"
    assert _to_metric_display("  ") == "N/A"
    assert _to_metric_display(" 42 ") == "42"

    assert _to_percent_display("80") == "80%"
    assert _to_percent_display("80%") == "80%"
    assert _to_percent_display(None) == "N/A"

    assert _to_float("3.14") == 3.14
    assert _to_float("bad") is None
    assert _to_int("7") == 7
    assert _to_int("7.0") is None


def test_store_returns_data_store_from_flask_extensions() -> None:
    app = Flask(__name__)
    sentinel = object()
    app.extensions["data_store"] = sentinel

    with app.app_context():
        assert _store() is sentinel
