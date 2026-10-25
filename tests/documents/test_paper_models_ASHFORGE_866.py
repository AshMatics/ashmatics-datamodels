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

"""RP-9 (ASHFORGE-866): paper tables and figures, the shared PerformanceMetric,
and the evidence document's abstract fields. KB design note IN-13 §1, §3.4, §4, §5."""

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.documents import (
    AbstractWitness,
    EvidenceContent,
    EvidenceDocument,
    EvidenceMetadataContent,
    EvidenceSummary,
    FigureReference,
    PaperFigure,
    PaperTable,
    PaperTableCell,
    PerformanceMetric,
    PerformanceTestResults,
    TableCellRef,
    TableReference,
)

SHA = "a" * 64


def _performance_table() -> PaperTable:
    """Table 2 of a typical diagnostic-accuracy paper: two header rows, a span."""
    header_1 = [
        PaperTableCell(text="Reader", col=0, row_span=2, column_header=True),
        PaperTableCell(text="Test set", col=1, col_span=2, column_header=True),
    ]
    header_2 = [
        PaperTableCell(text="Sensitivity, % (95% CI)", col=1, column_header=True),
        PaperTableCell(text="P value", col=2, column_header=True),
    ]
    body = [
        [
            PaperTableCell(text="AI", col=0, row_header=True),
            PaperTableCell.from_text("90.6 (82.2–95.9)ᵃ", 1, "Sensitivity, % (95% CI)"),
            PaperTableCell.from_text("<0.001", 2, "P value"),
        ],
        [
            PaperTableCell(text="Radiologists", col=0, row_header=True),
            PaperTableCell.from_text("84.1 (75.0–90.8)", 1, "Sensitivity, % (95% CI)"),
            PaperTableCell.from_text("—", 2, "P value"),
        ],
    ]
    return PaperTable(
        table_id="T2",
        label="Table 2",
        caption="Diagnostic performance on the external test set",
        footnotes=[{"mark": "a", "text": "Primary endpoint."}],
        pages=[5],
        bbox=[
            {
                "page": 5,
                "l": 50,
                "t": 700,
                "r": 550,
                "b": 500,
                "coord_origin": "bottom_left",
            }
        ],
        source={"parser": "docling", "version": "2.101.1"},
        header_rows=2,
        columns=[
            {"index": 0, "header_path": ["Reader"], "kind": "label"},
            {
                "index": 1,
                "header_path": ["Test set", "Sensitivity"],
                "unit": "% (95% CI)",
                "kind": "estimate_ci",
            },
            {"index": 2, "header_path": ["Test set", "P value"], "kind": "p_value"},
        ],
        rows=[header_1, header_2, *body],
        markdown="| Reader | Sensitivity | P |\n|---|---|---|\n| AI | 90.6 | <0.001 |",
        category="performance_metrics",
        category_confidence=0.93,
        merged_from=[],
        merge_method="none",
        merge_confidence=100.0,
        quality=[{"check": "ci_contains_value", "passed": True}],
    )


def _figure(**overrides) -> PaperFigure:
    fields = {
        "figure_id": "F3",
        "label": "Figure 3",
        "caption": "ROC curves of the AI system and eight readers.",
        "pages": [6],
        "source": {"parser": "jats"},
        "kind": "roc_curve",
        "kind_confidence": 0.88,
        "image": {"source_id": "src-42", "sha256": SHA, "width": 1200, "height": 900},
        "alt_text": "ROC curve; AUC 0.94.",
        "section": "Results",
        "evidence_id": "8f5b3c1e-0000-4000-8000-000000000001",
    }
    fields.update(overrides)
    return PaperFigure(**fields)


# =============================================================================
# PaperTable
# =============================================================================


class TestPaperTable:
    def test_valid_and_parsed(self):
        table = _performance_table()
        ai_sens = table.rows[2][1]
        assert ai_sens.parsed.kind == "estimate_interval"
        assert (ai_sens.parsed.value, ai_sens.parsed.ci_low) == (90.6, 82.2)
        assert ai_sens.parsed.unit == "%"
        assert ai_sens.footnote_marks == ["a"]
        assert table.rows[2][2].parsed.p_operator == "<"
        assert table.rows[3][2].parsed.kind == "not_reported"

    def test_round_trip(self):
        table = _performance_table()
        assert PaperTable.model_validate_json(table.model_dump_json()) == table
        assert PaperTable.model_validate(table.model_dump()) == table

    def test_cell_at_follows_spans(self):
        table = _performance_table()
        # "Reader" spans rows 0-1; "Test set" spans columns 1-2.
        assert table.cell_at(1, 0).text == "Reader"
        assert table.cell_at(0, 2).text == "Test set"
        assert table.cell_at(2, 1).text == "90.6 (82.2–95.9)ᵃ"
        assert table.cell_at(9, 0) is None
        assert table.cell_at(2, 7) is None

    def test_resolve_a_metric_cell_reference(self):
        table = _performance_table()
        assert (
            table.resolve(TableCellRef(table_id="T2", row=2, col=1)).parsed.value
            == 90.6
        )
        assert table.resolve(TableCellRef(table_id="T1", row=2, col=1)) is None

    def test_plausibility_problems_are_stored_not_refused(self):
        # Ragged row and a percentage over 100: §4.4 checks, recorded in quality.
        table = PaperTable(
            table_id="T1",
            source={"parser": "jats"},
            columns=[{"index": 0}, {"index": 1}],
            rows=[
                [PaperTableCell(text="a", col=0)],
                [
                    PaperTableCell.from_text("140%", 0),
                    PaperTableCell(text="x", col=1, col_span=4),
                ],
            ],
            quality=[
                {
                    "check": "column_count_consistent",
                    "passed": False,
                    "detail": "row 0",
                },
                {"check": "percent_in_range", "passed": False},
            ],
        )
        assert table.rows[1][0].parsed.value == 140.0

    @pytest.mark.parametrize(
        "change",
        [
            {"table_id": "Table 2"},
            {"table_id": "T0"},
            {"table_id": "t2"},
            {"category": "fda_predicate_comparison"},  # out of vocabulary: refused
            {"category": None},  # confidence without a category
            {"merge_confidence": 150.0},
            {"category_confidence": 1.5},
            {"header_rows": 9},
            {"pages": [0]},
            {"source": {"parser": "grobid"}},
            {"quality": [{"check": "Column Count", "passed": False}]},
            {"surprise": 1},
        ],
    )
    def test_invalid(self, change):
        payload = _performance_table().model_dump()
        payload.update(change)
        with pytest.raises(ValidationError):
            PaperTable.model_validate(payload)

    def test_columns_must_be_in_index_order(self):
        payload = _performance_table().model_dump()
        payload["columns"][0]["index"], payload["columns"][1]["index"] = 1, 0
        with pytest.raises(ValidationError, match="index order"):
            PaperTable.model_validate(payload)

    def test_cells_in_a_row_must_increase_by_column(self):
        payload = _performance_table().model_dump()
        payload["rows"][2].reverse()
        with pytest.raises(ValidationError, match="strictly increasing"):
            PaperTable.model_validate(payload)

    @pytest.mark.parametrize(
        "box",
        [
            {"page": 1, "l": 10, "t": 5, "r": 5, "b": 1, "coord_origin": "bottom_left"},
            {"page": 1, "l": 1, "t": 1, "r": 5, "b": 9, "coord_origin": "bottom_left"},
            {"page": 1, "l": 1, "t": 9, "r": 5, "b": 1, "coord_origin": "top_left"},
            {"page": 1, "l": 1, "t": 9, "r": 5, "b": 1},
        ],
    )
    def test_bad_bbox(self, box):
        payload = _performance_table().model_dump()
        payload["bbox"] = [box]
        with pytest.raises(ValidationError):
            PaperTable.model_validate(payload)

    def test_cell_invalid(self):
        with pytest.raises(ValidationError):
            PaperTableCell(text="x", col=-1)
        with pytest.raises(ValidationError):
            PaperTableCell(text="x", col=0, row_span=0)
        with pytest.raises(ValidationError):
            PaperTableCell(text="x")  # col is required


# =============================================================================
# PaperFigure
# =============================================================================


class TestPaperFigure:
    def test_valid_and_round_trip(self):
        figure = _figure()
        assert PaperFigure.model_validate_json(figure.model_dump_json()) == figure

    def test_generated_description_beside_missing_alt_text(self):
        figure = _figure(
            alt_text=None,
            generated_description={
                "text": "Two ROC curves; the AI curve lies above the readers' points.",
                "model": "claude-opus-5-5",
                "prompt_version": "figure-describe@1.0.0",
                "reason": "missing",
            },
        )
        assert figure.alt_text is None
        assert figure.generated_description.model == "claude-opus-5-5"

    def test_generated_description_beside_corrupt_alt_text(self):
        figure = _figure(
            alt_text="fig3_final_v2.tif",
            generated_description={
                "text": "ROC curves.",
                "model": "m",
                "prompt_version": "p@1",
                "reason": "filename",
            },
        )
        assert figure.alt_text == "fig3_final_v2.tif"  # kept as printed, never replaced

    def test_third_party_without_image(self):
        figure = _figure(
            image=None, third_party=True, third_party_marker="Reprinted with permission"
        )
        assert figure.image is None

    @pytest.mark.parametrize(
        "change",
        [
            {"figure_id": "fig1"},
            {"kind": "heatmap"},
            {"third_party": True},  # with the image still set
            {"third_party_marker": "©"},  # marker without the flag
            {"kind": None},  # kind_confidence without a kind
            {"image": {"source_id": "s", "sha256": "XYZ", "width": 1, "height": 1}},
            {"image": {"source_id": "s", "sha256": SHA, "width": 0, "height": 1}},
            {
                "generated_description": {
                    "text": "t",
                    "model": "m",
                    "prompt_version": "p",
                    "reason": "missing",
                }
            },  # alt_text is set, so it was not missing
            {
                "alt_text": None,
                "generated_description": {
                    "text": "t",
                    "model": "m",
                    "prompt_version": "p",
                    "reason": "mojibake",
                },
            },  # nothing to be corrupt
            {
                "alt_text": None,
                "generated_description": {
                    "text": "t",
                    "prompt_version": "p",
                    "reason": "missing",
                },
            },  # no model
            {"cited_by": [1, 2]},  # read from chunks, not stored
        ],
    )
    def test_invalid(self, change):
        with pytest.raises(ValidationError):
            _figure(**change)


# =============================================================================
# PerformanceMetric, shared (moved to documents/metrics.py)
# =============================================================================

PRE_0_23_METRIC = {
    "metric_name": "sensitivity",
    "metric_type": "sensitivity",
    "value": 0.906,
    "ci_lower": 0.822,
    "ci_upper": 0.959,
    "sample_size": 184,
    "stratification": {"study": "pivotal", "site": "multi_site"},
    "source_table": "table_18",
}


class TestPerformanceMetric:
    def test_regulatory_import_is_the_same_class(self):
        from ashmatics_datamodels.documents import metrics, regulatory

        assert regulatory.PerformanceMetric is metrics.PerformanceMetric
        assert regulatory.MetricType is metrics.MetricType

    def test_pre_0_23_payload_validates_unchanged(self):
        metric = PerformanceMetric.model_validate(PRE_0_23_METRIC)
        assert metric.model_dump(exclude_none=True) == PRE_0_23_METRIC
        results = PerformanceTestResults(performance_metrics=[PRE_0_23_METRIC])
        assert results.performance_metrics[0].source_table == "table_18"

    def test_page_and_cell(self):
        metric = PerformanceMetric(
            metric_name="Sensitivity",
            metric_type="sensitivity",
            value=90.6,
            unit="%",
            ci_lower=82.2,
            ci_upper=95.9,
            source_kind="table_cell",
            source_table="T2",
            source_page=5,
            source_cell={"table_id": "T2", "row": 2, "col": 1},
            source_text="90.6 (82.2–95.9)",
        )
        assert (
            _performance_table().resolve(metric.source_cell).parsed.value
            == metric.value
        )
        assert PerformanceMetric.model_validate_json(metric.model_dump_json()) == metric

    def test_fda_metric_with_a_page_and_cell(self):
        metric = PerformanceMetric(
            **PRE_0_23_METRIC,
            source_page=12,
            source_cell={"table_id": "table_18", "row": 3, "col": 2},
        )
        assert metric.source_cell.table_id == metric.source_table

    def test_from_the_abstract(self):
        # IN-13 decision 6: a non-OA paper's abstract may yield a metric record.
        metric = PerformanceMetric(
            metric_name="AUC",
            value=0.94,
            source_kind="abstract",
            source_text="AUC 0.94",
        )
        assert metric.source_cell is None

    @pytest.mark.parametrize(
        "change",
        [
            {"source_kind": "table_cell"},  # no cell
            {
                "source_kind": "abstract",
                "source_cell": {"table_id": "table_18", "row": 0, "col": 0},
            },
            {"source_cell": {"table_id": "table_19", "row": 0, "col": 0}},  # disagrees
            {"source_cell": {"table_id": "table_18", "row": -1, "col": 0}},
            {"source_cell": {"table_id": "", "row": 0, "col": 0}},
            {"source_page": 0},
            {"source_kind": "figure"},
        ],
    )
    def test_invalid(self, change):
        with pytest.raises(ValidationError):
            PerformanceMetric(**{**PRE_0_23_METRIC, **change})


# =============================================================================
# Evidence document: abstract, witnesses, paper tables and figures
# =============================================================================

# What the KB's evidence_document_store.put_record writes as metadata_content
# (with a content type it recognises).
KB_RECORD_METADATA_CONTENT = {
    "document_type": "kb_evidence_doc",
    "content_type": "peer_reviewed_paper",
    "title": "Deep learning for chest radiograph triage",
    "language": "en",
    "abstract": "Background: ... Results: AUC 0.94 ...",
    "publication_date": "2024-03-01",
    "authors": ["A. Author", "B. Author"],
    "journal": "Radiology",
    "doi": "10.1148/radiol.000000",
    "pubmed_id": "38000000",
}


class TestEvidenceAbstract:
    def test_abstract_is_a_field(self):
        assert "abstract" in EvidenceMetadataContent.model_fields

    def test_kb_record_metadata_content_validates(self):
        content = EvidenceMetadataContent.model_validate(KB_RECORD_METADATA_CONTENT)
        assert content.abstract.startswith("Background")
        assert content.abstract_witnesses is None

    def test_witnesses_round_trip(self):
        content = EvidenceMetadataContent.model_validate(
            {
                **KB_RECORD_METADATA_CONTENT,
                "abstract_witnesses": [
                    {
                        "source": "pubmed",
                        "text": "Background: ...",
                        "sha256": SHA,
                        "words": 248,
                        "retrieved_at": "2026-10-20T10:00:00Z",
                    },
                    {"source": "europepmc", "text": "Background ...", "words": 247},
                    {"source": "jats", "excluded": "abstract-type=summary"},
                ],
            }
        )
        assert content.abstract_witnesses[2].text is None
        again = EvidenceMetadataContent.model_validate_json(content.model_dump_json())
        assert again == content

    def test_pre_0_23_dump_gains_no_key(self):
        content = EvidenceMetadataContent.model_validate(KB_RECORD_METADATA_CONTENT)
        assert "abstract_witnesses" not in content.model_dump(exclude_none=True)

    @pytest.mark.parametrize(
        "witness",
        [
            {"source": "google_scholar", "text": "x"},
            {"source": "pubmed", "sha256": "not-a-hash"},
            {"source": "pubmed", "words": -1},
            {"source": "pubmed", "surprise": 1},
        ],
    )
    def test_invalid_witness(self, witness):
        with pytest.raises(ValidationError):
            AbstractWitness(**witness)

    def test_summary_carries_the_abstract(self):
        doc = EvidenceDocument(_id="e1", metadata_content=KB_RECORD_METADATA_CONTENT)
        assert (
            EvidenceSummary.from_document(doc).abstract == doc.metadata_content.abstract
        )


class TestEvidenceContentTablesAndFigures:
    def test_paper_and_legacy_items_side_by_side(self):
        legacy_table = {"table_id": "table1", "caption": "Old", "data": [{"a": 1}]}
        legacy_figure = {"figure_id": "F1", "caption": "Old figure"}
        content = EvidenceContent(
            sections={},
            tables=[legacy_table, _performance_table().model_dump()],
            figures=[legacy_figure, _figure().model_dump()],
        )
        assert isinstance(content.tables[0], TableReference)
        assert isinstance(content.tables[1], PaperTable)
        # A bare id and caption stays the legacy type, so old documents dump unchanged.
        assert isinstance(content.figures[0], FigureReference)
        assert isinstance(content.figures[1], PaperFigure)

    def test_document_round_trip(self):
        doc = EvidenceDocument(
            _id="e1",
            metadata_content=KB_RECORD_METADATA_CONTENT,
            content={
                "sections": {},
                "tables": [_performance_table()],
                "figures": [_figure()],
            },
        )
        again = EvidenceDocument.model_validate_json(doc.model_dump_json(by_alias=True))
        assert again == doc
        assert isinstance(again.content.tables[0], PaperTable)
        assert isinstance(again.content.figures[0], PaperFigure)

    def test_pre_0_23_document_dumps_unchanged(self):
        payload = {
            "_id": "e0",
            "metadata_content": KB_RECORD_METADATA_CONTENT,
            "content": {
                "sections": {},
                "tables": [
                    {
                        "table_id": "table1",
                        "caption": None,
                        "data": None,
                        "referenced_in_sections": [],
                        "metadata": {"markdown": "| a |"},
                    }
                ],
                "figures": [
                    {
                        "figure_id": "fig1",
                        "caption": "c",
                        "image_url": None,
                        "referenced_in_sections": [],
                    }
                ],
                "references": [],
            },
        }
        doc = EvidenceDocument.model_validate(payload)
        dumped = doc.model_dump(mode="json", by_alias=True)
        assert dumped["content"] == payload["content"]
