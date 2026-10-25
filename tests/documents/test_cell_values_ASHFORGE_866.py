# Copyright 2026 Asher Informatics PBC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The typed table-cell normaliser (ASHFORGE-866 RP-9, KB design note IN-13 §4)."""

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.documents import CellValue, normalise_cell

# (text, hint, expected fields). Fields not named must be None / empty.
CASES = [
    # No value
    ("", None, {"kind": "empty"}),
    ("   ", None, {"kind": "empty"}),
    (None, None, {"kind": "empty"}),
    ("*", None, {"kind": "empty", "footnote_marks": ["*"]}),
    ("—", None, {"kind": "not_reported"}),
    ("–", None, {"kind": "not_reported"}),
    ("-", None, {"kind": "not_reported"}),
    ("NR", None, {"kind": "not_reported"}),
    ("n/a", None, {"kind": "not_reported"}),
    ("Not reported", None, {"kind": "not_reported"}),
    ("NR", "n (%)", {"kind": "not_reported"}),
    # Numbers
    ("0.91", None, {"kind": "number", "value": 0.91}),
    ("1,234", None, {"kind": "number", "value": 1234.0}),
    ("0·95", None, {"kind": "number", "value": 0.95}),  # Lancet mid-dot decimal
    ("−0.5", None, {"kind": "number", "value": -0.5}),  # Unicode minus
    ("1e-5", None, {"kind": "number", "value": 1e-5}),
    ("12", "ms", {"kind": "number", "value": 12.0, "unit": "ms"}),
    ("12", "number", {"kind": "number", "value": 12.0}),
    # Percentages
    ("90.6%", None, {"kind": "percent", "value": 90.6, "unit": "%"}),
    ("90.6", "%", {"kind": "percent", "value": 90.6, "unit": "%"}),
    ("90.6", "percent", {"kind": "percent", "value": 90.6, "unit": "%"}),
    ("140%", None, {"kind": "percent", "value": 140.0, "unit": "%"}),  # a §4.4 check
    # n (%) and n/N
    (
        "45 (12.3%)",
        None,
        {"kind": "count_percent", "n": 45, "value": 12.3, "unit": "%"},
    ),
    (
        "45 (12.3)",
        "n (%)",
        {"kind": "count_percent", "n": 45, "value": 12.3, "unit": "%"},
    ),
    (
        "45 (12.3)",
        "count_percent",
        {"kind": "count_percent", "n": 45, "value": 12.3, "unit": "%"},
    ),
    (
        "1,045 (12.3%)",
        None,
        {"kind": "count_percent", "n": 1045, "value": 12.3, "unit": "%"},
    ),
    (
        "45/120 (37.5%)",
        None,
        {
            "kind": "count_percent",
            "n": 45,
            "denominator": 120,
            "value": 37.5,
            "unit": "%",
        },
    ),
    ("45/120", None, {"kind": "count_of_total", "n": 45, "denominator": 120}),
    # Estimate with an interval
    (
        "0.91 (0.85–0.95)",
        None,
        {"kind": "estimate_interval", "value": 0.91, "low": 0.85, "high": 0.95},
    ),
    (
        "0.91 [0.85, 0.95]",
        None,
        {"kind": "estimate_interval", "value": 0.91, "low": 0.85, "high": 0.95},
    ),
    (
        "0.91 (0.85–0.95)",
        "AUC (95% CI)",
        {
            "kind": "estimate_interval",
            "value": 0.91,
            "low": 0.85,
            "high": 0.95,
            "interval": "ci",
        },
    ),
    (
        "0.91 (95% CI: 0.85–0.95)",
        None,
        {
            "kind": "estimate_interval",
            "value": 0.91,
            "low": 0.85,
            "high": 0.95,
            "interval": "ci",
            "ci_level": 95.0,
        },
    ),
    (
        "90.6 (82.2–95.9)",
        "Sensitivity, % (95% CI)",
        {
            "kind": "estimate_interval",
            "value": 90.6,
            "low": 82.2,
            "high": 95.9,
            "interval": "ci",
            "unit": "%",
        },
    ),
    (
        "90.6% (82.2%-95.9%)",
        None,
        {
            "kind": "estimate_interval",
            "value": 90.6,
            "low": 82.2,
            "high": 95.9,
            "unit": "%",
        },
    ),
    (
        "54 (43–65)",
        "median [IQR]",
        {
            "kind": "estimate_interval",
            "value": 54.0,
            "low": 43.0,
            "high": 65.0,
            "interval": "iqr",
        },
    ),
    (
        "54 (43-65)",
        "median (range)",
        {
            "kind": "estimate_interval",
            "value": 54.0,
            "low": 43.0,
            "high": 65.0,
            "interval": "range",
        },
    ),
    (
        "−0.5 (−0.9 to −0.1)",
        None,
        {"kind": "estimate_interval", "value": -0.5, "low": -0.9, "high": -0.1},
    ),
    # Implausible but parsed as printed: value outside its own interval (a §4.4 check)
    (
        "0.99 (0.85–0.95)",
        None,
        {"kind": "estimate_interval", "value": 0.99, "low": 0.85, "high": 0.95},
    ),
    # mean ± SD
    ("54.2 ± 8.1", None, {"kind": "mean_sd", "value": 54.2, "plus_minus": 8.1}),
    ("54.2 +/- 8.1", None, {"kind": "mean_sd", "value": 54.2, "plus_minus": 8.1}),
    ("54.2 (8.1)", "mean (SD)", {"kind": "mean_sd", "value": 54.2, "plus_minus": 8.1}),
    ("54.2 (8.1)", "mean ± SD", {"kind": "mean_sd", "value": 54.2, "plus_minus": 8.1}),
    # Bare intervals
    ("12–45", None, {"kind": "interval", "low": 12.0, "high": 45.0}),
    ("12 to 45", None, {"kind": "interval", "low": 12.0, "high": 45.0}),
    (
        "12-45",
        "IQR",
        {"kind": "interval", "low": 12.0, "high": 45.0, "interval": "iqr"},
    ),
    (
        "0.85–0.95",
        "95% CI",
        {"kind": "interval", "low": 0.85, "high": 0.95, "interval": "ci"},
    ),
    # p-values
    ("p<0.001", None, {"kind": "p_value", "p_value": 0.001, "p_operator": "<"}),
    ("P = .03", None, {"kind": "p_value", "p_value": 0.03, "p_operator": "="}),
    ("p <= 0.05", None, {"kind": "p_value", "p_value": 0.05, "p_operator": "≤"}),
    ("<0.001", "P value", {"kind": "p_value", "p_value": 0.001, "p_operator": "<"}),
    ("0.03", "p", {"kind": "p_value", "p_value": 0.03, "p_operator": "="}),
    ("0.03", "p_value", {"kind": "p_value", "p_value": 0.03, "p_operator": "="}),
    # Footnote marks
    ("0.91*", None, {"kind": "number", "value": 0.91, "footnote_marks": ["*"]}),
    ("0.91**", None, {"kind": "number", "value": 0.91, "footnote_marks": ["**"]}),
    ("0.91†‡", None, {"kind": "number", "value": 0.91, "footnote_marks": ["†", "‡"]}),
    ("0.91ᵃ", None, {"kind": "number", "value": 0.91, "footnote_marks": ["a"]}),
    (
        "p ≤ 0.05*",
        None,
        {
            "kind": "p_value",
            "p_value": 0.05,
            "p_operator": "≤",
            "footnote_marks": ["*"],
        },
    ),
    # Never guessed: these stay text
    ("45 (12.3)", None, {"kind": "text"}),  # n (%) or mean (SD)? only a hint says
    ("<0.001", None, {"kind": "text"}),  # a bare bound is a p-value only in a p column
    ("p = 1.3", None, {"kind": "text"}),  # printed as a p-value, impossible as one
    ("-3-1", None, {"kind": "text"}),  # hyphen between signed numbers
    ("12 ms", None, {"kind": "text"}),
    ("Yes", None, {"kind": "text"}),
    ("1.2×10⁻³", None, {"kind": "text"}),  # the superscripts are an exponent, not marks
    ("45.5 (12.3%)", None, {"kind": "text"}),  # a count is a whole number
]


@pytest.mark.parametrize(("text", "hint", "expected"), CASES)
def test_normalise_cell(text, hint, expected):
    got = normalise_cell(text, hint)
    want = CellValue(**expected)
    assert got == want, f"{text!r} under {hint!r}: {got.model_dump(exclude_none=True)}"


def test_interval_kind_is_left_open_without_a_hint():
    cell = normalise_cell("0.91 (0.85–0.95)")
    assert cell.interval is None
    assert cell.ci_low is None and cell.ci_high is None
    assert (cell.low, cell.high) == (0.85, 0.95)


def test_ci_properties_read_only_a_confidence_interval():
    ci = normalise_cell("0.91 (0.85–0.95)", "95% CI")
    assert (ci.ci_low, ci.ci_high) == (0.85, 0.95)
    iqr = normalise_cell("54 (43–65)", "median [IQR]")
    assert iqr.ci_low is None and iqr.ci_high is None


def test_normaliser_is_pure():
    assert normalise_cell("45 (12.3%)") == normalise_cell("45 (12.3%)")
    assert normalise_cell("45 (12.3)", "n (%)") != normalise_cell("45 (12.3)")


class TestCellValueModel:
    def test_round_trip(self):
        cell = normalise_cell("90.6 (82.2–95.9)", "Sensitivity, % (95% CI)")
        assert CellValue.model_validate_json(cell.model_dump_json()) == cell
        assert CellValue.model_validate(cell.model_dump()) == cell

    @pytest.mark.parametrize(
        "payload",
        [
            {"kind": "fraction"},
            {"kind": "number", "p_value": 1.5},
            {"kind": "count_percent", "n": -1},
            {"kind": "count_of_total", "denominator": -3},
            {"kind": "mean_sd", "plus_minus": -1.0},
            {"kind": "estimate_interval", "interval": "credible"},
            {"kind": "p_value", "p_operator": "~"},
            {"kind": "estimate_interval", "ci_level": 100},
            {"kind": "number", "surprise": True},
        ],
    )
    def test_invalid(self, payload):
        with pytest.raises(ValidationError):
            CellValue(**payload)

    def test_plausibility_is_not_validated(self):
        # A §4.4 check, not a refusal: the table builder raises the finding.
        CellValue(kind="estimate_interval", value=2.0, low=0.1, high=0.2)
        CellValue(kind="percent", value=250.0, unit="%")


class TestDuoReviewFixes:
    """MR !13 review: an impossible CI level never raises; a header is not a unit."""

    @pytest.mark.parametrize(
        "cell", ["0.91 (100% CI: 0.85-0.95)", "0.91 (0% CI 0.85-0.95)"]
    )
    def test_out_of_range_ci_level_is_dropped(self, cell):
        out = normalise_cell(cell)
        assert out.kind == "estimate_interval"
        assert out.value == 0.91 and out.low == 0.85 and out.high == 0.95
        assert out.ci_level is None

    @pytest.mark.parametrize(
        ("hint", "unit"),
        [
            ("ms", "ms"),
            ("Age (years)", "years"),
            ("Weight, kg", "kg"),
            ("mg/dL", "mg/dL"),
            ("Specificity", None),
            ("Age", None),
            ("Positive predictive value (PPV)", None),
        ],
    )
    def test_plain_hint_unit(self, hint, unit):
        out = normalise_cell("12", hint)
        assert out.kind == "number"
        assert out.unit == unit
