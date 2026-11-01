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

"""Where a system document's parts are in their source, and where it was captured (0.25.0).

Additive: a 0.24.0 ``kb_ifu_doc`` or ``kb_aisystem_card`` validates unchanged. The
capture example is the front matter forge-collect-oracle writes for Oracle Health's
Confluence pages.
"""

import copy
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.documents import (
    SOURCE_LOCATION_KEYS,
    IfuContent,
    IfuDocument,
    IfuMetadataContent,
    SourceCapture,
    SourceLocation,
    SystemCardContent,
    SystemCardDocument,
    SystemCardMetadataContent,
    SystemDocumentSection,
    SystemDocumentTable,
)

SHA = "c646874ba659200a7846e115aa23699c2fea8558b4b28ef77866a2ebb014a945"

# The collector's front matter (source and provenance), as YAML loads it.
CAPTURE = {
    "system": "confluence",
    "url": "https://wiki.cerner.com/display/ModelCardsHP/Oracle+Health+Clinical+AI+Agent%2C+Smart+Dictation+Agent+Model+Card",
    "space": "ModelCardsHP",
    "page_id": "3508873444",
    "page_version": 15,
    "page_last_modified": "2026-08-26T19:20:58.000Z",
    "captured_at": "2026-11-01T01:10:46+00:00",
    "collector": "forge-collect-oracle/0.1.0",
    "content_sha256": SHA,
}

# A kb_ifu_doc as a 0.24.0 pipeline wrote it: no section metadata, no capture, a
# PDF table with pages and a Markdown table with source lines in free-form metadata.
IFU_024 = {
    "_id": "oracle-health/10006311",
    "metadata_content": {
        "document_type": "kb_ifu_doc",
        "content_type": "eifu",
        "title": "About Oracle Health Clinical AI Agent, Chart Review: Summaries Agent",
        "catalogue_number": "10006311",
        "product_name": "Oracle Health Clinical AI Agent, Chart Review: Summaries Agent",
        "manufacturer_name": "Cerner Corporation",
        "issue_date": "2026-08",
        "source_url": "https://wiki.cerner.com/",
        "source_printed_at": "2026-10-20T14:02:00Z",
    },
    "content": {
        "sections": {
            "description": {
                "title": "Description",
                "order": 1,
                "text": "a clinical documentation and chart review feature",
                "heading": "Description",
            },
            "cautions": {
                "title": "Cautions",
                "order": 2,
                "text": "No cautions exist for this product.",
                "stated_absent": True,
            },
        },
        "tables": [
            {
                "table_id": "table_1",
                "caption": None,
                "data": [{"Symbol": "[Catalogue Number]", "Meaning": "10006311"}],
                "metadata": {
                    "markdown": "| Symbol | Meaning |",
                    "header": ["Symbol", "Meaning"],
                    "pages": [1, 2],
                    "source_format": "pdf_ruled_cells",
                },
            },
            {
                "table_id": "table_2",
                "data": [],
                "metadata": {
                    "markdown": "| a |",
                    "header": ["a"],
                    "rows": [],
                    "source_lines": [40, 44],
                    "source_format": "markdown_table",
                },
            },
        ],
    },
}

CARD_024 = {
    "metadata_content": {
        "document_type": "kb_aisystem_card",
        "content_type": "system_card_hti1",
        "title": "Smart Dictation Agent Model Card",
        "system_name": "Oracle Health Clinical AI Agent, Smart Dictation Agent",
        "system_version": "26.09",
        "release_date": "2026-09",
    },
    "content": {
        "sections": {
            "external_validation": {
                "title": "External Validation",
                "order": 1,
                "text": "Not available. No external validation was conducted.",
                "stated_absent": True,
            }
        },
        "monitoring": [
            {"category": "performance", "metric": "Precision", "frequency": "Monthly"}
        ],
        "model_parts": [{"name": "GPT-5.4", "third_party": True}],
    },
}


def _without_new_keys(dump: dict) -> dict:
    """A dump with the 0.25.0 keys removed where they are None."""
    out = copy.deepcopy(dump)
    if out["metadata_content"].get("source_capture") is None:
        out["metadata_content"].pop("source_capture", None)
    for section in out["content"]["sections"].values():
        if section.get("metadata") is None:
            section.pop("metadata", None)
    return out


class TestOlderDocumentsUnchanged:
    @pytest.mark.parametrize(
        ("model", "payload"),
        [(IfuDocument, IFU_024), (SystemCardDocument, CARD_024)],
    )
    def test_024_document_validates_and_keeps_its_values(self, model, payload):
        doc = model.model_validate(copy.deepcopy(payload))
        assert doc.metadata_content.source_capture is None
        for section in doc.content.sections.values():
            assert section.metadata is None
        dump = _without_new_keys(doc.model_dump(by_alias=True, mode="json"))
        # Every value the 0.24.0 payload gave is dumped as it was given.
        for tier in ("metadata_content", "content"):
            for key, value in payload[tier].items():
                if key == "sections":
                    for name, section in value.items():
                        for k, v in section.items():
                            assert dump[tier]["sections"][name][k] == v, (name, k)
                elif key == "tables":
                    for i, table in enumerate(value):
                        for k, v in table.items():
                            assert dump[tier]["tables"][i][k] == v, (i, k)
                elif key == "source_printed_at":
                    assert datetime.fromisoformat(dump[tier][key]) == datetime(
                        2026, 10, 20, 14, 2, tzinfo=UTC
                    )
                elif key in ("monitoring", "model_parts"):
                    for i, row in enumerate(value):
                        for k, v in row.items():
                            assert dump[tier][key][i][k] == v
                else:
                    assert dump[tier][key] == value, key

    def test_table_metadata_dict_is_kept_whole(self):
        doc = IfuDocument.model_validate(copy.deepcopy(IFU_024))
        assert (
            doc.content.tables[0].metadata
            == IFU_024["content"]["tables"][0]["metadata"]
        )
        assert doc.content.tables[1].metadata["source_lines"] == [40, 44]
        assert isinstance(doc.content.tables[0], SystemDocumentTable)

    def test_new_keys_are_none_and_can_be_left_out_of_a_dump(self):
        """``exclude_none`` gives a dump a 0.24.0 install accepts."""
        doc = IfuDocument.model_validate(copy.deepcopy(IFU_024))
        dump = doc.model_dump(by_alias=True, exclude_none=True)
        assert "source_capture" not in dump["metadata_content"]
        assert all("metadata" not in s for s in dump["content"]["sections"].values())


class TestSourceLocation:
    def test_section_metadata_round_trips(self):
        section = SystemDocumentSection(
            title="Intended Use",
            order=3,
            text="...",
            metadata={"source_lines": [12, 20]},
        )
        assert section.metadata == SourceLocation(source_lines=(12, 20))
        assert section.metadata.pages is None
        again = SystemDocumentSection.model_validate(section.model_dump())
        assert again == section
        assert section.model_dump(mode="json")["metadata"] == {
            "source_lines": [12, 20],
            "pages": None,
        }

    def test_one_line_and_pages(self):
        loc = SourceLocation(source_lines=[7, 7], pages=[2, 3])
        assert loc.source_lines == (7, 7)
        assert loc.pages == [2, 3]

    @pytest.mark.parametrize(
        "lines",
        [
            [0, 3],  # 0 is not a 1-based line
            [5, 4],  # ends before it starts
            [3],  # not a pair
            [1, 2, 3],
            ["1", "2"],  # strings are not numbers
            [1.0, 2],
            [True, 2],
            "12-20",
        ],
    )
    def test_bad_source_lines_refused(self, lines):
        with pytest.raises(ValidationError):
            SourceLocation(source_lines=lines)
        with pytest.raises(ValidationError):
            SystemDocumentSection(title="t", order=1, metadata={"source_lines": lines})

    @pytest.mark.parametrize("pages", [[0], [1, -2], ["3"], [True], 3])
    def test_bad_pages_refused(self, pages):
        with pytest.raises(ValidationError):
            SourceLocation(pages=pages)

    def test_section_metadata_takes_no_other_key(self):
        with pytest.raises(ValidationError):
            SystemDocumentSection(
                title="t", order=1, metadata={"source_lines": [1, 2], "page": 3}
            )

    def test_table_source_lines_checked_other_keys_free(self):
        table = SystemDocumentTable(
            table_id="table_1",
            metadata={"source_lines": [3, 9], "markdown": "|a|", "anything": {"x": 1}},
        )
        assert table.metadata["anything"] == {"x": 1}
        assert SOURCE_LOCATION_KEYS == ("source_lines", "pages")

    @pytest.mark.parametrize(
        "metadata",
        [
            {"source_lines": [9, 3]},
            {"source_lines": [0, 1]},
            {"source_lines": "3-9"},
            {"pages": [0]},
            {"pages": ["1"]},
        ],
    )
    def test_bad_table_location_refused(self, metadata):
        with pytest.raises(ValidationError):
            SystemDocumentTable(table_id="t", metadata=metadata)
        with pytest.raises(ValidationError):
            IfuContent(tables=[{"table_id": "t", "metadata": metadata}])
        with pytest.raises(ValidationError):
            SystemCardContent(tables=[{"table_id": "t", "metadata": metadata}])

    def test_table_location_checked_on_assignment(self):
        table = SystemDocumentTable(table_id="t")
        with pytest.raises(ValidationError):
            table.metadata = {"source_lines": [2, 1]}


class TestSourceCapture:
    def test_collector_front_matter_round_trips_on_both_documents(self):
        ifu = IfuDocument(
            metadata_content=IfuMetadataContent(
                title="t",
                catalogue_number="10006311",
                product_name="p",
                source_capture=CAPTURE,
            )
        )
        card = SystemCardDocument(
            metadata_content=SystemCardMetadataContent(
                title="t", system_name="s", source_capture=CAPTURE
            )
        )
        for doc in (ifu, card):
            cap = doc.metadata_content.source_capture
            assert cap.system == "confluence"
            assert cap.page_id == "3508873444"
            assert cap.page_version == 15
            assert cap.page_last_modified == datetime(
                2026, 8, 26, 19, 20, 58, tzinfo=UTC
            )
            assert cap.captured_at == datetime(2026, 11, 1, 1, 10, 46, tzinfo=UTC)
            assert cap.content_sha256 == SHA
            assert type(doc).model_validate(doc.model_dump(by_alias=True)) == doc
            assert (
                type(doc).model_validate(doc.model_dump(by_alias=True, mode="json"))
                == doc
            )

    def test_only_the_required_fields(self):
        cap = SourceCapture(
            system="web",
            url="http://example.org/page",
            captured_at="2026-11-01T01:10:46Z",
            collector="c/1",
            content_sha256=SHA,
        )
        assert cap.page_id is None
        assert cap.page_version is None
        assert cap.page_last_modified is None
        assert cap.space is None

    def test_numeric_page_id_kept_as_text(self):
        assert SourceCapture(**{**CAPTURE, "page_id": 3508873444}).page_id == (
            "3508873444"
        )

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("system", "Confluence"),
            ("system", ""),
            ("url", "wiki.cerner.com/display/x"),
            ("url", "ftp://wiki.cerner.com/x"),
            ("url", "https://wiki.cerner.com/a b"),
            ("page_id", ""),
            ("page_id", "a b"),
            ("page_id", True),
            ("page_version", 0),
            ("page_version", "15"),
            ("page_version", True),
            ("page_last_modified", "last Tuesday"),
            ("captured_at", "2026-13-01T00:00:00Z"),
            ("captured_at", None),
            ("collector", ""),
            ("content_sha256", SHA.upper()),
            ("content_sha256", SHA[:-1]),
            ("content_sha256", SHA + "0"),
            ("content_sha256", "z" * 64),
        ],
    )
    def test_bad_shapes_refused(self, field, value):
        with pytest.raises(ValidationError):
            SourceCapture(**{**CAPTURE, field: value})

    @pytest.mark.parametrize(
        "missing", ["system", "url", "captured_at", "collector", "content_sha256"]
    )
    def test_required(self, missing):
        payload = {k: v for k, v in CAPTURE.items() if k != missing}
        with pytest.raises(ValidationError):
            SourceCapture(**payload)

    def test_unknown_key_refused(self):
        """The collector's other front matter (labels, page_created) is not taken."""
        with pytest.raises(ValidationError):
            SourceCapture(**{**CAPTURE, "page_created": None})
