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

"""
The typed table-cell normaliser (0.23.0, ASHFORGE-866 RP-9).

One function, :func:`normalise_cell`, turns the text of a table cell as printed
into a :class:`CellValue`: numbers, percentages, ``n (%)``, ``n/N``, an estimate
with its interval, ``mean ± SD``, a bare interval, p-values, and the dashes and
``NR`` that mean "no value". It is pure: no I/O, no state, the same answer for
the same input.

**It never guesses.** A form that means different things under different column
headers (``45 (12.3)`` is ``n (%)`` or ``mean (SD)``; ``0.91 (0.85-0.95)`` has a
CI, an IQR or a range) is resolved only by the ``hint`` (the column's unit as
printed, or a :class:`ColumnKind` value). Without a hint the cell is ``text``, or
the interval kind is left ``None``, and the table checks (IN-13 §4.4, numeric parse
rate) see it.

**It never refuses a value for being implausible.** A percentage of 140, a value
outside its own interval, an ``n (%)`` whose arithmetic is wrong: all are parsed
as printed. Those are the §4.4 checks, raised as findings by the table builder;
a model that refused them would lose the table and the finding with it.
"""

from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Literal

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel

# =============================================================================
# Vocabularies
# =============================================================================


class CellValueKind(str, Enum):
    """What a cell's text was parsed as."""

    EMPTY = "empty"  # Blank, or footnote marks only
    NOT_REPORTED = "not_reported"  # "—", "-", "NR", "N/A", "not reported": no value
    NUMBER = "number"  # 0.91, 1,234, 12 (with the hint's unit, if any)
    PERCENT = "percent"  # 90.6%
    COUNT_PERCENT = "count_percent"  # 45 (12.3%), 45/120 (37.5%)
    COUNT_OF_TOTAL = "count_of_total"  # 45/120
    ESTIMATE_INTERVAL = "estimate_interval"  # 0.91 (0.85-0.95), 54 [43, 65]
    MEAN_SD = "mean_sd"  # 54.2 ± 8.1, or 54.2 (8.1) under an SD hint
    INTERVAL = "interval"  # 0.85-0.95, 12 to 45: two bounds, no estimate
    P_VALUE = "p_value"  # p<0.001, P = .03, or 0.03 under a p hint
    TEXT = "text"  # Anything else, including every ambiguous form


class IntervalKind(str, Enum):
    """What a pair of bounds is. ``None`` on a cell means the print does not say."""

    CI = "ci"  # Confidence interval (from "95% CI" in the cell, or a CI hint)
    IQR = "iqr"  # Interquartile range (from the hint)
    RANGE = "range"  # Minimum to maximum (from the hint)


class ColumnKind(str, Enum):
    """What a table column holds, as the table builder decides from its header.

    IN-13 §4.1 names ``label``, ``number``, ``count_percent``, ``estimate_ci`` and
    ``text``; the rest are the header units the same section lists (``%``,
    ``mean ± SD``, ``median [IQR]``) and the forms :func:`normalise_cell` parses.
    Every value is also accepted as a ``hint``.
    """

    LABEL = "label"
    NUMBER = "number"
    PERCENT = "percent"
    COUNT_PERCENT = "count_percent"
    COUNT_OF_TOTAL = "count_of_total"
    ESTIMATE_CI = "estimate_ci"
    MEAN_SD = "mean_sd"
    MEDIAN_IQR = "median_iqr"
    RANGE = "range"
    P_VALUE = "p_value"
    TEXT = "text"


PValueOperator = Literal["=", "<", "≤", ">", "≥"]


# =============================================================================
# The parsed value
# =============================================================================


class CellValue(AshMaticsBaseModel):
    """A table cell's text, parsed. Every field but ``kind`` is optional.

    ``low``/``high`` are the bounds of whatever interval was printed, and
    ``interval`` says which kind it is when the print or the hint says so;
    ``ci_low``/``ci_high`` read them only when it is a confidence interval.
    Plausibility (percent in 0..100, ``low <= value <= high``) is deliberately
    not validated here: see the module docstring.
    """

    kind: CellValueKind = Field(..., description="What the text was parsed as")
    value: float | None = Field(
        None,
        description=(
            "The number: the estimate, the mean, the percentage of an n (%) cell, "
            "or the plain number. Percentages are on the printed 0-100 scale"
        ),
    )
    unit: str | None = Field(
        None, description="'%' when printed or hinted, else the hint's plain unit"
    )
    low: float | None = Field(None, description="Lower bound of the printed interval")
    high: float | None = Field(None, description="Upper bound of the printed interval")
    interval: IntervalKind | None = Field(
        None, description="ci, iqr or range; None when neither print nor hint says"
    )
    ci_level: float | None = Field(
        None, gt=0, lt=100, description="Confidence level when printed, e.g. 95"
    )
    plus_minus: float | None = Field(
        None, ge=0, description="The ± term of a mean ± SD cell"
    )
    p_value: float | None = Field(None, ge=0.0, le=1.0, description="The p-value")
    p_operator: PValueOperator | None = Field(
        None, description="How the p-value was printed: '=', '<', '≤', '>', '≥'"
    )
    n: int | None = Field(None, ge=0, description="The count of an n (%) or n/N cell")
    denominator: int | None = Field(None, ge=0, description="The N of an n/N cell")
    footnote_marks: list[str] = Field(
        default_factory=list,
        description="Trailing marks stripped before parsing (*, †, ‡, superscripts)",
    )

    @property
    def ci_low(self) -> float | None:
        """``low`` when the interval is a confidence interval, else None."""
        return self.low if self.interval == IntervalKind.CI.value else None

    @property
    def ci_high(self) -> float | None:
        """``high`` when the interval is a confidence interval, else None."""
        return self.high if self.interval == IntervalKind.CI.value else None


# =============================================================================
# The normaliser
# =============================================================================

_NOT_REPORTED = frozenset(
    {
        "-",
        "–",
        "—",
        "−",
        "‒",
        "--",
        "nr",
        "n/r",
        "na",
        "n/a",
        "n.a.",
        "ne",
        "not reported",
        "not available",
        "not applicable",
        "not estimable",
        "...",
        "…",
    }
)

_MARK_SYMBOLS = "*†‡§¶‖#"

_INT = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
_NUM = (
    r"(?:[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?"
    r"|[-+]?\.\d+(?:[eE][-+]?\d+)?)"
)
_SEP = r"(–|-|to|,|;)"
_OPS = r"(=|<|>|≤|≥)"

_RE_P_PREFIX = re.compile(rf"p\s*{_OPS}\s*({_NUM})", re.IGNORECASE)
_RE_P_BARE = re.compile(rf"{_OPS}?\s*({_NUM})")
_RE_COUNT_TOTAL_PCT = re.compile(
    rf"({_INT})\s*/\s*({_INT})\s*[(\[]\s*({_NUM})\s*(%)?\s*[)\]]"
)
_RE_COUNT_PCT = re.compile(rf"({_INT})\s*[(\[]\s*({_NUM})\s*(%)?\s*[)\]]")
_RE_ESTIMATE_INTERVAL = re.compile(
    rf"({_NUM})\s*(%)?\s*[(\[]\s*"
    rf"(?:(\d+(?:\.\d+)?)\s*%\s*CI\s*[:,]?\s*)?"
    rf"({_NUM})\s*(%)?\s*{_SEP}\s*({_NUM})\s*(%)?\s*[)\]]",
    re.IGNORECASE,
)
_RE_MEAN_SD = re.compile(rf"({_NUM})\s*(%)?\s*±\s*({_NUM})\s*(%)?")
_RE_MEAN_PAREN = re.compile(rf"({_NUM})\s*(%)?\s*[(\[]\s*({_NUM})\s*(%)?\s*[)\]]")
_RE_COUNT_TOTAL = re.compile(rf"({_INT})\s*/\s*({_INT})")
_RE_INTERVAL = re.compile(
    rf"({_NUM})\s*(%)?\s*(–|-|to)\s*({_NUM})\s*(%)?", re.IGNORECASE
)
_RE_PERCENT = re.compile(rf"({_NUM})\s*%")
_RE_NUMBER = re.compile(_NUM)


class _Hint(str, Enum):
    COUNT_PERCENT = "count_percent"
    SD = "sd"
    IQR = "iqr"
    RANGE = "range"
    CI = "ci"
    P = "p"
    PERCENT = "percent"
    PLAIN = "plain"


_KIND_HINTS = {
    ColumnKind.COUNT_PERCENT.value: _Hint.COUNT_PERCENT,
    ColumnKind.MEAN_SD.value: _Hint.SD,
    ColumnKind.MEDIAN_IQR.value: _Hint.IQR,
    ColumnKind.RANGE.value: _Hint.RANGE,
    ColumnKind.ESTIMATE_CI.value: _Hint.CI,
    ColumnKind.P_VALUE.value: _Hint.P,
    ColumnKind.PERCENT.value: _Hint.PERCENT,
}


# Units a bare hint may name. A header word that is not a unit ("Specificity",
# "Age") is not one, so a hint outside this set and without a unit symbol gives
# no unit rather than a wrong one.
_KNOWN_UNITS = frozenset(
    """s sec ms min h hr hrs hour hours d day days wk week weeks mo month months
    y yr yrs year years nm um µm mm cm m km mg g kg ml l dl mmhg bpm gy mgy msv
    hu kv kvp mas px pixels voxels""".split()
)
_UNIT_SYMBOL = re.compile(r"^[^\s]{1,12}$")  # one token: mg/dL, mm², m^2, °C


def _plain_unit(hint: str) -> str | None:
    """The unit a non-keyword hint names, or ``None`` when it names none.

    ``"ms"`` and ``"Age (years)"`` give ``ms`` and ``years``; ``"Weight, kg"``
    gives ``kg``; ``"Specificity"`` and ``"Positive predictive value (PPV)"``
    give ``None``. A candidate is the trailing parenthetical, else the text after
    the last comma, else the whole hint.
    """
    h = " ".join(hint.split())
    m = re.search(r"\(([^()]+)\)\s*$", h)
    candidate = m.group(1) if m else h.rsplit(",", 1)[-1]
    candidate = candidate.strip()
    if candidate.casefold() in _KNOWN_UNITS:
        return candidate
    if _UNIT_SYMBOL.fullmatch(candidate) and re.search(r"[/^²³°µ]", candidate):
        return candidate
    return None


def _classify_hint(hint: str | None) -> tuple[_Hint | None, bool]:
    """Classify a hint; the flag says the hint puts the values in percent.

    The ``95% CI`` of a header such as ``Sensitivity, % (95% CI)`` is a level,
    not a unit, so it is taken out before looking for ``%``.
    """
    if hint is None:
        return None, False
    h = " ".join(hint.split()).casefold()
    if not h:
        return None, False
    if h in _KIND_HINTS:
        kind = _KIND_HINTS[h]
        return kind, kind == _Hint.PERCENT
    if h in {kind.value for kind in ColumnKind}:
        return None, False  # label, number, count_of_total, text: nothing to carry
    if re.search(r"\b(n|no\.?)\s*\(\s*%\s*\)", h):
        return _Hint.COUNT_PERCENT, False
    pct = "%" in re.sub(r"\d+(?:\.\d+)?\s*%\s*ci\b", "", h)
    if re.search(r"\biqr\b", h):
        return _Hint.IQR, pct
    if re.search(r"\brange\b", h):
        return _Hint.RANGE, pct
    if re.search(r"\bsd\b", h) or "±" in h:
        return _Hint.SD, pct
    if re.search(r"\bci\b", h):
        return _Hint.CI, pct
    if re.fullmatch(r"p(\s*-?\s*values?)?", h):
        return _Hint.P, False
    if pct:
        return _Hint.PERCENT, True
    return _Hint.PLAIN, False


def _is_mark_char(ch: str) -> bool:
    if ch in "\u207a\u207b":  # superscript + and -: an exponent (10⁻³), not a mark
        return False
    return ch in _MARK_SYMBOLS or unicodedata.decomposition(ch).startswith("<super>")


def _strip_marks(text: str) -> tuple[str, list[str]]:
    """Take trailing footnote marks off ``text``; one mark per symbol run."""
    runs: list[str] = []
    rest = text
    if re.search(r"[\u207a\u207b][\u00b2\u00b3\u00b9\u2070-\u2079]+$", text):
        return text, []  # 10⁻³: the trailing superscripts are an exponent
    while rest and _is_mark_char(rest[-1]):
        ch = rest[-1]
        end = len(rest)
        start = end - 1
        if ch in _MARK_SYMBOLS:
            while start > 0 and rest[start - 1] == ch:
                start -= 1
        else:
            while (
                start > 0
                and rest[start - 1] not in _MARK_SYMBOLS
                and _is_mark_char(rest[start - 1])
            ):
                start -= 1
        runs.append(rest[start:end])
        rest = rest[:start].rstrip()
    marks: list[str] = []
    for run in reversed(runs):
        if run[0] in _MARK_SYMBOLS:
            marks.append(run)
        else:
            marks.extend(m for m in unicodedata.normalize("NFKC", run).split(",") if m)
    return rest, marks


def _canonical(text: str) -> str:
    """Collapse whitespace and spell signs, dashes, decimals and ± one way."""
    text = " ".join(text.split())
    text = re.sub(r"(?<=\d)·(?=\d)", ".", text)  # Lancet mid-dot decimal: 0·95
    text = text.replace("−", "-").replace("‐", "-").replace("‑", "-")
    text = text.replace("—", "–").replace("‒", "–")
    text = text.replace("<=", "≤").replace(">=", "≥")
    text = text.replace("+/-", "±").replace("+/−", "±")
    return text


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _int(s: str) -> int:
    return int(s.replace(",", ""))


def _signed(s: str) -> bool:
    return s.startswith(("-", "+"))


def _interval_for(hint: _Hint | None, ci_level: str | None) -> IntervalKind | None:
    if ci_level is not None or hint == _Hint.CI:
        return IntervalKind.CI
    if hint == _Hint.IQR:
        return IntervalKind.IQR
    if hint == _Hint.RANGE:
        return IntervalKind.RANGE
    return None


def normalise_cell(text: str | None, hint: str | None = None) -> CellValue:
    """Parse one table cell's printed text into a :class:`CellValue`.

    Args:
        text: The cell as printed. ``None`` is treated as an empty cell.
        hint: The column's unit as printed in its header (``"%"``, ``"n (%)"``,
            ``"mean ± SD"``, ``"median [IQR]"``, ``"95% CI"``, ``"P value"``,
            ``"ms"``), or a :class:`ColumnKind` value. It resolves the forms that
            are ambiguous on their own and supplies the unit of a bare number. A
            header with no keyword gives a unit only when it names one
            (``"Age (years)"``: ``years``; ``"Specificity"``: none).

    Returns:
        A ``CellValue``. Text that matches no form, or matches one only a hint
        could resolve when there is none, is ``kind="text"``.
    """
    rest, marks = _strip_marks(" ".join((text or "").split()))
    hint_kind, hint_percent = _classify_hint(hint)
    plain_unit = _plain_unit(hint) if hint_kind == _Hint.PLAIN and hint else None
    hinted_unit = "%" if hint_percent else plain_unit

    def make(kind: CellValueKind, **fields: object) -> CellValue:
        return CellValue(kind=kind, footnote_marks=marks, **fields)  # type: ignore[arg-type]

    if not rest:
        return make(CellValueKind.EMPTY)
    if rest.casefold() in _NOT_REPORTED:
        return make(CellValueKind.NOT_REPORTED)

    s = _canonical(rest)

    # p-values: "p<0.001", "P = .03" anywhere; bare "<0.001" or "0.03" only under a p hint.
    m = _RE_P_PREFIX.fullmatch(s)
    if m or hint_kind == _Hint.P:
        m = m or _RE_P_BARE.fullmatch(s)
        if m:
            p = _num(m.group(2))
            if 0.0 <= p <= 1.0:
                return make(
                    CellValueKind.P_VALUE, p_value=p, p_operator=m.group(1) or "="
                )
        if _RE_P_PREFIX.fullmatch(s):
            return make(
                CellValueKind.TEXT
            )  # "p = 1.3": printed as a p-value, impossible

    # n/N (%): unambiguous, the parentheses can only be the percentage.
    m = _RE_COUNT_TOTAL_PCT.fullmatch(s)
    if m:
        return make(
            CellValueKind.COUNT_PERCENT,
            n=_int(m.group(1)),
            denominator=_int(m.group(2)),
            value=_num(m.group(3)),
            unit="%",
        )

    # n (%): the % sign or an n (%) hint says so; otherwise "45 (12.3)" is ambiguous.
    m = _RE_COUNT_PCT.fullmatch(s)
    if m and (m.group(3) or hint_kind == _Hint.COUNT_PERCENT):
        return make(
            CellValueKind.COUNT_PERCENT,
            n=_int(m.group(1)),
            value=_num(m.group(2)),
            unit="%",
        )

    # estimate (low-high), estimate [low, high], estimate (95% CI low-high)
    m = _RE_ESTIMATE_INTERVAL.fullmatch(s)
    if m and not (m.group(6) == "-" and (_signed(m.group(4)) or _signed(m.group(7)))):
        level = m.group(3)
        has_pct = any(m.group(i) for i in (2, 5, 8))
        return make(
            CellValueKind.ESTIMATE_INTERVAL,
            value=_num(m.group(1)),
            low=_num(m.group(4)),
            high=_num(m.group(7)),
            interval=_interval_for(hint_kind, level),
            # CellValue bounds ci_level to (0, 100); an impossible printed level is
            # dropped, never raised, so one cell cannot sink a whole table.
            ci_level=float(level) if level and 0 < float(level) < 100 else None,
            unit="%" if has_pct else hinted_unit,
        )

    # mean ± SD, or mean (SD) under an SD hint
    m = _RE_MEAN_SD.fullmatch(s)
    if m is None and hint_kind == _Hint.SD:
        m = _RE_MEAN_PAREN.fullmatch(s)
    if m and not _signed(m.group(3)):
        return make(
            CellValueKind.MEAN_SD,
            value=_num(m.group(1)),
            plus_minus=_num(m.group(3)),
            unit="%" if (m.group(2) or m.group(4)) else hinted_unit,
        )

    m = _RE_COUNT_TOTAL.fullmatch(s)
    if m:
        return make(
            CellValueKind.COUNT_OF_TOTAL,
            n=_int(m.group(1)),
            denominator=_int(m.group(2)),
        )

    # A bare interval. A hyphen separates only unsigned bounds ("-3-1" is not read).
    m = _RE_INTERVAL.fullmatch(s)
    if m and not (m.group(3) == "-" and (_signed(m.group(1)) or _signed(m.group(4)))):
        return make(
            CellValueKind.INTERVAL,
            low=_num(m.group(1)),
            high=_num(m.group(4)),
            interval=_interval_for(hint_kind, None),
            unit="%" if (m.group(2) or m.group(5)) else hinted_unit,
        )

    m = _RE_PERCENT.fullmatch(s)
    if m:
        return make(CellValueKind.PERCENT, value=_num(m.group(1)), unit="%")

    if _RE_NUMBER.fullmatch(s):
        value = _num(s)
        if hint_percent:
            return make(CellValueKind.PERCENT, value=value, unit="%")
        return make(CellValueKind.NUMBER, value=value, unit=plain_unit)

    return make(CellValueKind.TEXT)
