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

"""Vendor system documents: kb_ifu_doc and kb_aisystem_card (ASHFORGE-827, SC-9n).

The examples are the Oracle Health Chart Review documents the Knowledgebase design
(DESIGN-Function-Concepts-And-Summary-Enrichment-20261027, section 7) is read from.
"""

import pytest
from pydantic import ValidationError

import ashmatics_datamodels.documents as documents
from ashmatics_datamodels.documents import (
    IFU_SECTION_NAMES,
    SYSTEM_CARD_SECTION_NAMES,
    ContentType,
    DocumentType,
    IfuContent,
    IfuDocument,
    IfuMetadataContent,
    ModelPart,
    MonitoringCategory,
    MonitoringMetric,
    PerformanceMetrics,
    SystemCardContent,
    SystemCardDocument,
    SystemCardMetadataContent,
    SystemDocumentSection,
)


def _section(order: int, text: str, **kw) -> SystemDocumentSection:
    return SystemDocumentSection(
        title=kw.pop("title", "t"), order=order, text=text, **kw
    )


class TestVocabulary:
    def test_document_types(self):
        assert DocumentType.IFU_DOC.value == "kb_ifu_doc"
        assert DocumentType.AISYSTEM_CARD.value == "kb_aisystem_card"

    def test_model_card_kind_is_gone(self):
        """kb_aimodel_card was replaced by kb_aisystem_card (7.10): one card kind."""
        assert "kb_aimodel_card" not in {t.value for t in DocumentType}
        assert not hasattr(DocumentType, "AIMODEL_CARD")
        assert "model_card_v1" not in {t.value for t in ContentType}
        for name in (
            "ModelCardDocument",
            "ModelCardDocumentCreate",
            "ModelCardMetadataContent",
            "ModelCardContent",
            "ModelCardSummary",
        ):
            assert not hasattr(documents, name), name
            assert name not in documents.__all__, name

    def test_content_types(self):
        assert ContentType.SYSTEM_CARD_HTI1.value == "system_card_hti1"
        assert ContentType.EIFU.value == "eifu"


class TestIfuDocument:
    def _metadata(self, **kw) -> IfuMetadataContent:
        return IfuMetadataContent(
            title="About Oracle Health Clinical AI Agent, Chart Review: Summaries Agent",
            catalogue_number="10006311",
            product_name="Oracle Health Clinical AI Agent, Chart Review: Summaries Agent",
            manufacturer_name="Cerner Corporation",
            issue_date="2026-08",
            **kw,
        )

    def test_defaults_and_sections(self):
        doc = IfuDocument(
            metadata_content=self._metadata(),
            content=IfuContent(
                sections={
                    "description": _section(
                        1, "a clinical documentation and chart review feature"
                    ),
                    "cautions": _section(
                        2, "No cautions exist for this product.", stated_absent=True
                    ),
                }
            ),
        )
        assert doc.metadata_content.document_type == "kb_ifu_doc"
        assert doc.metadata_content.content_type == "eifu"
        assert doc.content.sections["cautions"].stated_absent is True
        assert doc.content.sections["description"].stated_absent is False

    def test_round_trip(self):
        doc = IfuDocument(metadata_content=self._metadata())
        again = IfuDocument.model_validate(doc.model_dump(by_alias=True))
        assert again == doc

    def test_unknown_section_refused(self):
        with pytest.raises(ValidationError, match="unknown IFU section"):
            IfuContent(sections={"licence": _section(1, "...")})

    def test_every_listed_section_accepted(self):
        sections = {n: _section(i + 1, n) for i, n in enumerate(IFU_SECTION_NAMES)}
        assert set(IfuContent(sections=sections).sections) == set(IFU_SECTION_NAMES)

    def test_catalogue_number_required_and_key_shaped(self):
        with pytest.raises(ValidationError):
            IfuMetadataContent(title="t", product_name="p")  # no catalogue number
        with pytest.raises(ValidationError):
            IfuMetadataContent(
                title="t", product_name="p", catalogue_number="100 06311"
            )

    @pytest.mark.parametrize(
        "value", ["2026-8", "August 2026", "2026-13", "2026-08-32"]
    )
    def test_issue_date_shape(self, value):
        with pytest.raises(ValidationError):
            IfuMetadataContent(
                title="t", catalogue_number="1", product_name="p", issue_date=value
            )

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            self._metadata(catalog_number="typo")


class TestSystemCardDocument:
    def _metadata(self) -> SystemCardMetadataContent:
        return SystemCardMetadataContent(
            title="Oracle Health AI Agents, Chart Review: Conversational Search Agent (Physicians) Model Card",
            system_name="Oracle Health AI Agents, Chart Review: Conversational Search Agent (Physicians)",
            system_version="26.09",
            release_date="2026-09",
            model_type="Summarization and retrieval",
            developer="Oracle Health",
            third_party_information="OpenAI Platform",
            source_url="https://wiki.cerner.com/",
        )

    def test_card_with_monitoring_and_model_parts(self):
        doc = SystemCardDocument(
            metadata_content=self._metadata(),
            content=SystemCardContent(
                sections={
                    "external_validation": _section(
                        1,
                        "Not available. No external validation was conducted.",
                        stated_absent=True,
                        heading="External Validation",
                    ),
                    "development": _section(
                        2, "variables identified in 45 CFR 170.213"
                    ),
                },
                monitoring=[
                    MonitoringMetric(
                        category=MonitoringCategory.PERFORMANCE,
                        metric="Precision",
                        method="Clinician review of sampled summaries",
                        automated_or_manual="Manual",
                        frequency="Monthly",
                        acceptable_range=">= 0.9",
                        mitigation="Prompt revision",
                    ),
                    MonitoringMetric(
                        category="bias_fairness", metric="Recall by subgroup"
                    ),
                ],
                model_parts=[
                    ModelPart(
                        name="GPT-5.4", role="large language model", third_party=True
                    ),
                    ModelPart(
                        name="Nomic embeddings", role="embeddings", third_party=True
                    ),
                    ModelPart(
                        name="BGE reranker",
                        role="reranker",
                        performance=PerformanceMetrics(
                            additional_metrics={"recall@10": 0.8}
                        ),
                    ),
                ],
            ),
        )
        assert doc.metadata_content.document_type == "kb_aisystem_card"
        assert doc.metadata_content.content_type == "system_card_hti1"
        assert [m.category for m in doc.content.monitoring] == [
            "performance",
            "bias_fairness",
        ]
        assert doc.content.monitoring[1].method is None
        assert [p.name for p in doc.content.model_parts] == [
            "GPT-5.4",
            "Nomic embeddings",
            "BGE reranker",
        ]
        again = SystemCardDocument.model_validate(doc.model_dump(by_alias=True))
        assert again == doc

    def test_zero_model_parts_and_no_monitoring_table(self):
        """A card that writes monitoring as prose has no rows; parts are optional."""
        doc = SystemCardDocument(metadata_content=self._metadata())
        assert doc.content.monitoring == []
        assert doc.content.model_parts == []

    def test_unknown_section_refused(self):
        with pytest.raises(ValidationError, match="unknown system card section"):
            SystemCardContent(sections={"model_overview": _section(1, "...")})

    def test_every_listed_section_accepted(self):
        sections = {
            n: _section(i + 1, n) for i, n in enumerate(SYSTEM_CARD_SECTION_NAMES)
        }
        content = SystemCardContent(sections=sections)
        assert set(content.sections) == set(SYSTEM_CARD_SECTION_NAMES)

    def test_monitoring_category_closed(self):
        with pytest.raises(ValidationError):
            MonitoringMetric(category="cost", metric="x")
        assert {c.value for c in MonitoringCategory} == {
            "performance",
            "bias_fairness",
            "safety",
            "kpi",
        }

    def test_system_name_required(self):
        with pytest.raises(ValidationError):
            SystemCardMetadataContent(title="t")

    def test_model_part_metrics_range(self):
        with pytest.raises(ValidationError):
            PerformanceMetrics(accuracy=1.5)
