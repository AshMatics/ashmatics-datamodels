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
Structured tables and figures of a research paper (0.23.0, ASHFORGE-866 RP-9).

``PaperTable`` and ``PaperFigure`` are what the ``research-paper`` ingestion
profile (KB design note IN-13, §4 and §5) stores in ``content.tables`` and
``content.figures`` of a ``kb_evidence_doc`` full-text document. A table is a
cell grid with header rows, spans, footnote marks and, per cell, the value the
typed normaliser (``documents.cell_values``) read from it; a figure is a record
with its caption, kind, author alt text kept apart from any generated
description, and an image reference only where the licence allows one.

What the models enforce is **structure** (ids, positions, one state per field
pair). What they deliberately do not enforce is **plausibility**: a ragged row,
a percentage over 100 or a value outside its interval are the IN-13 §4.4 checks,
which the table builder records in ``quality`` and raises as findings. The licence
rule (no table, no image without a full-text licence) is the landing contract's,
because only the evidence row knows the licence.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from itertools import pairwise
from typing import Annotated

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.documents.cell_values import (
    CellValue,
    ColumnKind,
    normalise_cell,
)
from ashmatics_datamodels.documents.metrics import TableCellRef

# =============================================================================
# Vocabularies
# =============================================================================


class PaperParser(str, Enum):
    """Which parser produced a table or figure."""

    JATS = "jats"  # Publisher XML; the table of record when present (IN-13 §4.4)
    DOCLING = "docling"  # PDF layout parser


class PaperTableCategory(str, Enum):
    """What a paper table is about (IN-13 §4.3). Out-of-vocabulary is refused."""

    COHORT_DEMOGRAPHICS = "cohort_demographics"
    DATASET_DESCRIPTION = "dataset_description"
    PERFORMANCE_METRICS = "performance_metrics"
    COMPARISON = "comparison"
    SUBGROUP_PERFORMANCE = "subgroup_performance"
    READER_STUDY = "reader_study"
    CALIBRATION_OR_THRESHOLD = "calibration_or_threshold"
    CLINICAL_OUTCOMES = "clinical_outcomes"
    SAFETY_OR_FAILURES = "safety_or_failures"
    INCLUDED_STUDIES = "included_studies"
    RISK_OF_BIAS = "risk_of_bias"
    OTHER = "other"


class PaperFigureKind(str, Enum):
    """What a paper figure shows (IN-13 §5)."""

    ROC_CURVE = "roc_curve"
    FOREST_PLOT = "forest_plot"
    FLOW_DIAGRAM = "flow_diagram"  # CONSORT, STARD
    ARCHITECTURE = "architecture"
    EXAMPLE_IMAGES = "example_images"
    CHART = "chart"
    TABLE_AS_IMAGE = "table_as_image"
    OTHER = "other"


class CoordOrigin(str, Enum):
    """Where a bounding box's y axis starts (docling's ``coord_origin``)."""

    TOP_LEFT = "top_left"
    BOTTOM_LEFT = "bottom_left"


class GeneratedDescriptionReason(str, Enum):
    """Why a figure description was generated (IN-13 decision 7)."""

    MISSING = "missing"  # No author alt text at all
    EMPTY = "empty"  # Author alt text present but blank
    TRUNCATED = "truncated"
    FILENAME = "filename"  # The "alt text" is a file name
    MOJIBAKE = "mojibake"  # Encoding damage


PageNumber = Annotated[int, Field(ge=1)]


# =============================================================================
# Shared pieces
# =============================================================================


class BoundingBox(AshMaticsBaseModel):
    """Where on a page a table or figure sits (from docling ``prov``)."""

    page: int = Field(..., ge=1, description="1-based page number")
    l: float = Field(..., description="Left edge")  # noqa: E741 (docling's name)
    t: float = Field(..., description="Top edge")
    r: float = Field(..., description="Right edge")
    b: float = Field(..., description="Bottom edge")
    coord_origin: CoordOrigin = Field(
        ...,
        description="Origin of the y axis; decides whether t is above b numerically",
    )

    @model_validator(mode="after")
    def _edges_are_ordered(self) -> BoundingBox:
        if self.l > self.r:
            raise ValueError(f"left edge {self.l} is right of right edge {self.r}")
        if self.coord_origin == CoordOrigin.TOP_LEFT.value and self.t > self.b:
            raise ValueError("with a top-left origin, t must not exceed b")
        if self.coord_origin == CoordOrigin.BOTTOM_LEFT.value and self.b > self.t:
            raise ValueError("with a bottom-left origin, b must not exceed t")
        return self


class PaperParserSource(AshMaticsBaseModel):
    """The parser that produced a table or figure, and its version."""

    parser: PaperParser = Field(..., description="jats or docling")
    version: str | None = Field(
        None, description="Parser version, e.g. docling 2.101.1"
    )


# =============================================================================
# Tables
# =============================================================================


class PaperFootnote(AshMaticsBaseModel):
    """One table footnote; ``mark`` is the symbol cells carry in ``footnote_marks``."""

    mark: str | None = Field(
        None, description="The footnote mark (a, *, †), if printed"
    )
    text: str = Field(..., min_length=1, description="The footnote text")


class PaperTableColumn(AshMaticsBaseModel):
    """One column: every header level above it, its unit and what it holds."""

    index: int = Field(..., ge=0, description="0-based column position")
    header_path: list[str] = Field(
        default_factory=list,
        description="Every header level, top first: ['Test set', 'AI', 'Sensitivity']",
    )
    unit: str | None = Field(
        None,
        description="Unit from the header: '%', 'n (%)', 'mean ± SD', 'median [IQR]', 'ms'",
    )
    kind: ColumnKind | None = Field(None, description="What the column holds")


class PaperTableCell(AshMaticsBaseModel):
    """One cell, at its top-left grid position.

    A cell spanning several rows appears once, in the row where it starts; rows
    below it have no cell at the covered positions. ``parsed`` is the normaliser's
    reading of ``text`` (None when not parsed, e.g. a header cell).
    """

    text: str = Field(
        "", description="The cell exactly as printed (whitespace trimmed)"
    )
    col: int = Field(..., ge=0, description="0-based column where the cell starts")
    row_span: int = Field(1, ge=1, description="Rows the cell covers")
    col_span: int = Field(1, ge=1, description="Columns the cell covers")
    column_header: bool = Field(False, description="A column header cell")
    row_header: bool = Field(False, description="A row header (row label) cell")
    footnote_marks: list[str] = Field(
        default_factory=list, description="Footnote marks on the cell, as printed"
    )
    parsed: CellValue | None = Field(None, description="The typed value read from text")

    @classmethod
    def from_text(
        cls, text: str, col: int, hint: str | None = None, **fields: object
    ) -> PaperTableCell:
        """Build a cell and parse its text with :func:`normalise_cell`.

        ``hint`` is the column's unit (or kind). The marks the normaliser
        strips become the cell's ``footnote_marks`` unless given explicitly.
        """
        parsed = normalise_cell(text, hint)
        fields.setdefault("footnote_marks", list(parsed.footnote_marks))
        return cls(text=text, col=col, parsed=parsed, **fields)  # type: ignore[arg-type]


class PaperTableQualityCheck(AshMaticsBaseModel):
    """One IN-13 §4.4 check on a table, passed or failed (a failure is a finding)."""

    check: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Check name, e.g. column_count_consistent, ci_contains_value",
    )
    passed: bool = Field(..., description="Whether the table passed the check")
    detail: str | None = Field(None, description="What failed, where")


class PaperTable(AshMaticsBaseModel):
    """One table of a research paper as structured data (IN-13 §4.1)."""

    table_id: str = Field(
        ...,
        pattern=r"^T[1-9][0-9]*$",
        description="T1, T2... in document order; stable across re-extraction",
    )
    label: str | None = Field(
        None, description="As printed: 'Table 2', 'Supplementary Table S1'"
    )
    caption: str | None = Field(None, description="The caption")
    footnotes: list[PaperFootnote] = Field(default_factory=list)
    pages: list[PageNumber] = Field(
        default_factory=list, description="1-based pages (docling prov); empty for JATS"
    )
    bbox: list[BoundingBox] = Field(
        default_factory=list,
        description="One box per page (docling prov); empty for JATS",
    )
    source: PaperParserSource = Field(..., description="Parser and version")
    header_rows: int = Field(0, ge=0, description="How many leading rows are headers")
    columns: list[PaperTableColumn] = Field(default_factory=list)
    rows: list[list[PaperTableCell]] = Field(
        default_factory=list, description="The grid, header rows first"
    )
    markdown: str | None = Field(
        None,
        description="docling's markdown (or rendered from JATS), for chunks and review",
    )
    category: PaperTableCategory | None = Field(None, description="IN-13 §4.3 category")
    category_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Classifier confidence, 0-1"
    )
    merged_from: list[str] = Field(
        default_factory=list,
        description="Table ids the consolidator merged into this one",
    )
    merge_method: str | None = Field(None, description="Consolidator method, as FDA's")
    merge_confidence: float | None = Field(
        None, ge=0.0, le=100.0, description="Consolidator confidence, 0-100 as FDA's"
    )
    quality: list[PaperTableQualityCheck] = Field(
        default_factory=list, description="The IN-13 §4.4 checks, each pass or fail"
    )

    @model_validator(mode="after")
    def _grid_is_well_formed(self) -> PaperTable:
        for position, column in enumerate(self.columns):
            if column.index != position:
                raise ValueError(
                    f"columns[{position}].index is {column.index}; columns are in index order"
                )
        for r, row in enumerate(self.rows):
            cols = [cell.col for cell in row]
            if any(a >= b for a, b in pairwise(cols)):
                raise ValueError(
                    f"row {r}: cells must be in strictly increasing col order"
                )
        if self.header_rows > len(self.rows):
            raise ValueError(
                f"header_rows is {self.header_rows} but the table has {len(self.rows)} rows"
            )
        if self.category_confidence is not None and self.category is None:
            raise ValueError("category_confidence without a category")
        return self

    def cell_at(self, row: int, col: int) -> PaperTableCell | None:
        """The cell covering grid position (row, col), spans included, or None."""
        for r in range(min(row, len(self.rows) - 1), -1, -1):
            for cell in self.rows[r]:
                if (
                    r + cell.row_span > row
                    and cell.col <= col < cell.col + cell.col_span
                ):
                    return cell
        return None

    def resolve(self, ref: TableCellRef) -> PaperTableCell | None:
        """The cell a metric's ``source_cell`` points at, if it is in this table."""
        if ref.table_id != self.table_id:
            return None
        return self.cell_at(ref.row, ref.col)


# =============================================================================
# Figures
# =============================================================================


class FigureImage(AshMaticsBaseModel):
    """A figure's PNG, stored through ``POST /ingestion/sources``."""

    source_id: str = Field(..., min_length=1, description="The ingestion source id")
    sha256: str = Field(
        ...,
        pattern=r"^[0-9a-f]{64}$",
        description="sha256 of the PNG bytes, lowercase hex",
    )
    width: int = Field(..., ge=1, description="Pixels")
    height: int = Field(..., ge=1, description="Pixels")


class GeneratedDescription(AshMaticsBaseModel):
    """A machine-written figure description (IN-13 decision 7). Never alt text."""

    text: str = Field(..., min_length=1, description="The generated description")
    model: str = Field(..., min_length=1, description="Model that wrote it")
    prompt_version: str = Field(..., min_length=1, description="Prompt id and version")
    reason: GeneratedDescriptionReason = Field(
        ..., description="Why: author alt text missing, or how it was corrupt"
    )
    generated_at: datetime | None = Field(None, description="When it was generated")


class PaperFigure(AshMaticsBaseModel):
    """One figure of a research paper (IN-13 §5).

    Which text chunks cite the figure is not stored here: chunks carry
    ``cites.figures`` and the figure's list is read back by query, so there is
    one source of truth.
    """

    figure_id: str = Field(
        ..., pattern=r"^F[1-9][0-9]*$", description="F1, F2... in document order"
    )
    label: str | None = Field(None, description="As printed: 'Figure 3', 'Fig. 2b'")
    caption: str | None = Field(None, description="The caption")
    pages: list[PageNumber] = Field(default_factory=list, description="1-based pages")
    bbox: list[BoundingBox] = Field(default_factory=list)
    source: PaperParserSource | None = Field(None, description="Parser and version")
    kind: PaperFigureKind | None = Field(None, description="What the figure shows")
    kind_confidence: float | None = Field(None, ge=0.0, le=1.0)
    image: FigureImage | None = Field(
        None,
        description="The stored PNG; null unless the licence permits full text, "
        "and always null for third-party material",
    )
    third_party: bool = Field(
        False,
        description="The caption marks third-party material (raises figure_third_party)",
    )
    third_party_marker: str | None = Field(
        None, description="The caption text that marked it: 'Reprinted with permission'"
    )
    alt_text: str | None = Field(
        None,
        description="The publisher's own alt text (JATS alt-text or long-desc) only",
    )
    generated_description: GeneratedDescription | None = Field(
        None,
        description="Written when alt text is missing or corrupt; kept apart from it",
    )
    section: str | None = Field(None, description="The section the figure sits in")
    evidence_id: str | None = Field(None, description="Back link: the evidence row id")
    document_id: str | None = Field(
        None, description="Back link: the full-text document id"
    )

    @model_validator(mode="after")
    def _states_agree(self) -> PaperFigure:
        if self.third_party and self.image is not None:
            raise ValueError("a third-party figure carries no image")
        if self.third_party_marker is not None and not self.third_party:
            raise ValueError("third_party_marker set but third_party is false")
        if self.kind_confidence is not None and self.kind is None:
            raise ValueError("kind_confidence without a kind")
        generated = self.generated_description
        if generated is not None:
            missing = generated.reason == GeneratedDescriptionReason.MISSING.value
            if missing and self.alt_text is not None:
                raise ValueError("reason 'missing' but the figure has alt_text")
            if not missing and self.alt_text is None:
                raise ValueError(
                    f"reason {generated.reason!r} describes alt text, but alt_text is null"
                )
        return self
