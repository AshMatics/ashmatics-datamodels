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
Vendor system documents in ``kb_documents``: instructions for use and AI system cards.

Two document kinds (ASHFORGE-827, the Knowledgebase's SC-9n,
``DESIGN-Function-Concepts-And-Summary-Enrichment-20261027`` sections 7.2, 7.5 and
7.10), each bound to an ``ash:DocumentKindScheme`` concept:

- ``kb_ifu_doc`` (``IfuDocument``): a manufacturer's instructions for use, printed
  or electronic. Labelling, not a submission, so not ``kb_regulatory_doc``, and the
  kind says nothing about whether the product is regulated.
- ``kb_aisystem_card`` (``SystemCardDocument``): a vendor's card for a deployed AI
  system or decision support intervention as a whole. A vendor's ONC HTI-1
  source-attribute document is one even when the vendor titles it a model card: it
  describes orchestration, third-party models, workflow, human review and
  monitoring. The models inside are ``ModelPart`` entries, zero or more; there is no
  model-card document kind (it replaced ``kb_aimodel_card`` in 0.24.0).

Section text is verbatim. A section the document says is absent ("No cautions
exist ...", "Not available. ...") is kept with ``stated_absent=True``; a section
the document does not have is left out. Section keys are the stable names in
``IFU_SECTION_NAMES`` and ``SYSTEM_CARD_SECTION_NAMES``; any other key is refused.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import Field, field_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.documents.base import (
    ContentBase,
    ContentType,
    DocumentType,
    MetadataContentBase,
    MetadataObjectBase,
    MongoDocumentBase,
    SectionBase,
)

# A release or issue month as the KB stores it: YYYY-MM, or YYYY-MM-DD when the
# document gives a day. "September 2026" is "2026-09".
YearMonth = Annotated[
    str,
    Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?$"),
]

# =============================================================================
# Section names (the keys of content.sections)
# =============================================================================

# kb_ifu_doc: the IFU content of EU MDR Annex I section 23.4, as the eIFU headings
# print it. Catalogue number, manufacturer block and date are metadata, not
# sections. Licence, patents, warranty, copyright and additional resources stay in
# the markdown only.
IFU_SECTION_NAMES: tuple[str, ...] = (
    "description",
    "intended_use",
    "indications_for_use",
    "intended_users",
    "intended_patient_population",
    "clinical_benefits",
    "performance_characteristics",
    "safety_information",
    "cautions",
    "warnings",
    "contraindications",
    "user_training",
    "cybersecurity",
    "incident_reporting",
)

# kb_aisystem_card: the 45 CFR 170.315(b)(11) source attributes, as the HTI-1
# headings print them. "Primary Intended Use and Users" is one section per table
# row; the quantitative, external-validation and maintenance headings split as
# their sub-headings do.
SYSTEM_CARD_SECTION_NAMES: tuple[str, ...] = (
    "model_summary",
    "intervention_output",
    "intended_use",
    "intended_patient_population",
    "intended_users",
    "decision_making_role",
    "out_of_scope_uses",
    "development",
    "fairness",
    "test_data_validity",
    "test_data_fairness",
    "evaluation_references",
    "external_validation",
    "external_data_validity",
    "external_data_fairness",
    "local_data_validity",
    "local_data_fairness",
    "monitoring",
    "maintenance",
)


def _check_section_names(
    sections: dict[str, Any], allowed: tuple[str, ...], kind: str
) -> None:
    unknown = sorted(set(sections) - set(allowed))
    if unknown:
        raise ValueError(
            f"unknown {kind} section name(s) {unknown}; allowed: {list(allowed)}"
        )


class SystemDocumentSection(SectionBase):
    """One section of an IFU or system card, its text verbatim."""

    heading: str | None = Field(
        None,
        description="The heading as the document prints it",
    )
    stated_absent: bool = Field(
        False,
        description=(
            "True when the document states the content is absent ('No cautions "
            "exist ...', 'Not available. ...'). The text keeps the statement: "
            "'no external validation was conducted' is a fact a hazard analysis uses."
        ),
    )


# =============================================================================
# kb_ifu_doc: instructions for use
# =============================================================================


class IfuMetadataContent(MetadataContentBase):
    """Metadata of an instructions-for-use document, as the document writes it."""

    document_type: DocumentType = Field(
        default=DocumentType.IFU_DOC,
        description="Always 'kb_ifu_doc'",
    )
    content_type: ContentType = Field(
        default=ContentType.EIFU,
        description="IFU format",
    )

    catalogue_number: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9.-]{1,40}$",
        description="Catalogue number (one IFU per number; a revision is new content of the same document)",
    )
    product_name: str = Field(
        ...,
        description="Product name as the document writes it",
    )
    manufacturer_name: str | None = Field(
        None,
        description="Legal manufacturer as the manufacturer block writes it",
    )
    manufacturer_address: str | None = Field(
        None,
        description="The manufacturer block's address, verbatim",
    )
    issue_date: YearMonth | None = Field(
        None,
        description="Issue date of this revision, YYYY-MM (or YYYY-MM-DD)",
    )
    source_url: str | None = Field(
        None,
        description="Where the document is published",
    )
    source_printed_at: datetime | None = Field(
        None,
        description="The time in the print header, when the source is a printed web page",
    )


class IfuContent(ContentBase):
    """Content of an instructions-for-use document."""

    sections: dict[str, SystemDocumentSection] = Field(  # type: ignore[assignment]
        default_factory=dict,
        description="Sections keyed by IFU_SECTION_NAMES; absent sections are left out",
    )

    @field_validator("sections")
    @classmethod
    def _known_sections(
        cls, sections: dict[str, SystemDocumentSection]
    ) -> dict[str, SystemDocumentSection]:
        _check_section_names(sections, IFU_SECTION_NAMES, "IFU")
        return sections


class IfuDocument(MongoDocumentBase):
    """A ``kb_ifu_doc`` document with the three-tier structure."""

    metadata_object: MetadataObjectBase = Field(
        default_factory=MetadataObjectBase,
        description="Artifact metadata",
    )
    metadata_content: IfuMetadataContent = Field(
        ...,
        description="IFU metadata",
    )
    content: IfuContent = Field(
        default_factory=IfuContent,
        description="IFU sections",
    )


class IfuDocumentCreate(MongoDocumentBase):
    """Schema for creating a ``kb_ifu_doc`` document."""

    metadata_content: IfuMetadataContent = Field(
        ...,
        description="Required IFU metadata",
    )
    content: IfuContent = Field(
        default_factory=IfuContent,
        description="IFU sections",
    )


# =============================================================================
# kb_aisystem_card: monitoring
# =============================================================================


class MonitoringCategory(str, Enum):
    """The group a monitoring metric is listed under on an HTI-1 card."""

    PERFORMANCE = "performance"
    BIAS_FAIRNESS = "bias_fairness"
    SAFETY = "safety"
    KPI = "kpi"


class MonitoringMetric(AshMaticsBaseModel):
    """One row of a card's monitoring table, its cells verbatim.

    The six-column table (metric, method, automated or manual, frequency,
    acceptable range, mitigation) under its group heading. Rows stay on the
    document, versioned and promoted with it; nothing compares them across systems
    yet. An empty cell is ``None``.
    """

    category: MonitoringCategory = Field(
        ...,
        description="The group heading the row is listed under",
    )
    metric: str = Field(
        ...,
        description="What is monitored",
    )
    method: str | None = Field(
        None,
        description="How it is measured",
    )
    automated_or_manual: str | None = Field(
        None,
        description="Automated or manual, as printed",
    )
    frequency: str | None = Field(
        None,
        description="How often, as printed",
    )
    acceptable_range: str | None = Field(
        None,
        description="The acceptable range or threshold, as printed",
    )
    mitigation: str | None = Field(
        None,
        description="What is done when the metric leaves its range, as printed",
    )


# =============================================================================
# kb_aisystem_card: model parts (the former model-card fields)
# =============================================================================


class InputSpecs(AshMaticsBaseModel):
    """Model input specifications."""

    image_size: list[int] | None = Field(
        None,
        description="Input image dimensions [height, width]",
    )
    channels: int | None = Field(
        None,
        description="Number of input channels",
    )
    format: str | None = Field(
        None,
        description="Input format (e.g., 'DICOM', 'PNG')",
    )
    additional_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional input specifications",
    )


class OutputSpecs(AshMaticsBaseModel):
    """Model output specifications."""

    classes: list[str] = Field(
        default_factory=list,
        description="Output class labels",
    )
    output_format: str | None = Field(
        None,
        description="Output format (e.g., 'probability_distribution', 'bounding_boxes')",
    )
    additional_outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional output specifications",
    )


class DataSplits(AshMaticsBaseModel):
    """Training data split ratios."""

    train: float = Field(0.7, ge=0.0, le=1.0, description="Training set ratio")
    val: float = Field(0.15, ge=0.0, le=1.0, description="Validation set ratio")
    test: float = Field(0.15, ge=0.0, le=1.0, description="Test set ratio")


class ModelTrainingData(AshMaticsBaseModel):
    """What a model part was trained on."""

    dataset_name: str | None = Field(None, description="Name of training dataset")
    dataset_size: int | None = Field(
        None, ge=0, description="Number of samples in dataset"
    )
    data_splits: DataSplits | None = Field(
        None, description="Train/val/test split ratios"
    )
    data_source: str | None = Field(None, description="Source of training data")
    inclusion_criteria: str | None = Field(None, description="Data inclusion criteria")
    exclusion_criteria: str | None = Field(None, description="Data exclusion criteria")


class PerformanceMetrics(AshMaticsBaseModel):
    """A model part's headline performance metrics (0-1)."""

    accuracy: float | None = Field(None, ge=0.0, le=1.0, description="Overall accuracy")
    sensitivity: float | None = Field(
        None, ge=0.0, le=1.0, description="Sensitivity (recall)"
    )
    specificity: float | None = Field(None, ge=0.0, le=1.0, description="Specificity")
    auc_roc: float | None = Field(
        None, ge=0.0, le=1.0, description="Area under ROC curve"
    )
    f1_score: float | None = Field(None, ge=0.0, le=1.0, description="F1 score")
    validation_dataset: str | None = Field(
        None, description="Dataset used for validation"
    )
    additional_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Additional metrics"
    )


class ExternalResources(AshMaticsBaseModel):
    """Links to external resources about a model part."""

    github: str | None = Field(None, description="GitHub repository URL")
    huggingface: str | None = Field(None, description="Hugging Face model URL")
    paper_doi: str | None = Field(None, description="DOI of associated paper")
    documentation: str | None = Field(
        None, description="Documentation URL, such as the model's own model card"
    )


class ModelPart(AshMaticsBaseModel):
    """One model inside an AI system: what a model card would describe.

    A card names its models (a third-party LLM, an embedding model, a reranker);
    each is a part of the system, never a document of its own. Every field but the
    name is optional, because most system cards name a model and say little else
    about it.
    """

    name: str = Field(
        ..., description="Model name as the card writes it (e.g., 'GPT-5.4')"
    )
    version: str | None = Field(None, description="Model version")
    role: str | None = Field(
        None,
        description="What the model does in the system, as the card writes it (e.g., 'embeddings', 'reranker')",
    )
    model_type: str | None = Field(
        None, description="Model type (e.g., 'large language model')"
    )
    developer: str | None = Field(None, description="Who developed the model")
    third_party: bool | None = Field(
        None,
        description="True when the model is a third party's, not the system developer's",
    )
    architecture: str | None = Field(
        None, description="Model architecture (e.g., 'ResNet-50', 'ViT-B/16')"
    )
    framework: str | None = Field(
        None, description="ML framework (e.g., 'PyTorch 2.0')"
    )
    input_specs: InputSpecs | None = Field(None, description="Input specifications")
    output_specs: OutputSpecs | None = Field(None, description="Output specifications")
    training_data: ModelTrainingData | None = Field(None, description="Training data")
    performance: PerformanceMetrics | None = Field(
        None, description="Headline performance metrics"
    )
    limitations: list[str] = Field(
        default_factory=list, description="Known limitations"
    )
    external_resources: ExternalResources | None = Field(
        None, description="Links to external resources"
    )


# =============================================================================
# kb_aisystem_card: metadata, content, document
# =============================================================================


class SystemCardMetadataContent(MetadataContentBase):
    """Metadata of an AI system card: the HTI-1 Model Summary, as the card writes it."""

    document_type: DocumentType = Field(
        default=DocumentType.AISYSTEM_CARD,
        description="Always 'kb_aisystem_card'",
    )
    content_type: ContentType = Field(
        default=ContentType.SYSTEM_CARD_HTI1,
        description="Card format",
    )

    system_name: str = Field(
        ...,
        description="The Model Summary's name: the system as the card writes it",
    )
    system_version: str | None = Field(
        None,
        description="The Model Summary's version (a release of the system, e.g., '26.09')",
    )
    release_date: YearMonth | None = Field(
        None,
        description="The Model Summary's release date, YYYY-MM (or YYYY-MM-DD)",
    )
    model_type: str | None = Field(
        None,
        description="The Model Summary's model type, verbatim (e.g., 'Summarization and retrieval')",
    )
    description: str | None = Field(
        None,
        description="The Model Summary's description, verbatim",
    )
    developer: str | None = Field(
        None,
        description="The Model Summary's developer",
    )
    funding_source: str | None = Field(
        None,
        description="The Model Summary's funding source, verbatim",
    )
    third_party_information: str | None = Field(
        None,
        description="The Model Summary's third-party information, verbatim (e.g., the LLM platform)",
    )
    source_url: str | None = Field(
        None,
        description="Where the card is published",
    )
    source_printed_at: datetime | None = Field(
        None,
        description="The time in the print header, when the source is a printed web page",
    )


class SystemCardContent(ContentBase):
    """Content of an AI system card."""

    sections: dict[str, SystemDocumentSection] = Field(  # type: ignore[assignment]
        default_factory=dict,
        description="Sections keyed by SYSTEM_CARD_SECTION_NAMES; absent sections are left out",
    )
    monitoring: list[MonitoringMetric] = Field(
        default_factory=list,
        description="Rows of the card's monitoring table, when it has one; a card that writes monitoring as prose has none",
    )
    model_parts: list[ModelPart] = Field(
        default_factory=list,
        description="The models inside the system, zero or more",
    )

    @field_validator("sections")
    @classmethod
    def _known_sections(
        cls, sections: dict[str, SystemDocumentSection]
    ) -> dict[str, SystemDocumentSection]:
        _check_section_names(sections, SYSTEM_CARD_SECTION_NAMES, "system card")
        return sections


class SystemCardDocument(MongoDocumentBase):
    """A ``kb_aisystem_card`` document with the three-tier structure."""

    metadata_object: MetadataObjectBase = Field(
        default_factory=MetadataObjectBase,
        description="Artifact metadata",
    )
    metadata_content: SystemCardMetadataContent = Field(
        ...,
        description="System card metadata",
    )
    content: SystemCardContent = Field(
        default_factory=SystemCardContent,
        description="System card sections, monitoring and model parts",
    )


class SystemCardDocumentCreate(MongoDocumentBase):
    """Schema for creating a ``kb_aisystem_card`` document."""

    metadata_content: SystemCardMetadataContent = Field(
        ...,
        description="Required system card metadata",
    )
    content: SystemCardContent = Field(
        default_factory=SystemCardContent,
        description="System card sections, monitoring and model parts",
    )
