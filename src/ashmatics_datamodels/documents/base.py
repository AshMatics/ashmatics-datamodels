# Copyright 2025 Asher Informatics PBC
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
Base schemas for MongoDB document three-tier structure.

All kb_* MongoDB collections follow this standardized pattern:
- Tier 1: metadata_object - Artifact/file metadata
- Tier 2: metadata_content - Content classification metadata
- Tier 3: content - Actual document body with sections

Reference: docs/Plans/DocumentDataModelSchema-Normalize-2025-11-15/
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel

# =============================================================================
# Document Type Enumerations
# =============================================================================


class DocumentType(str, Enum):
    """The kb_documents ``document_type`` discriminator — the KIND axis.

    Single-sourced from the ontology ``ash:DocumentKindScheme`` (ASHKBAPP-91,
    ADR-002 Decision 5). Each value is the exact stored token and must equal the
    scheme's ``skos:notation``; the ADR-002 CI guard
    (tests/documents/test_ontology_binding.py) fails on drift. Regulator scoping
    is NOT encoded here — it lives on the sibling ``regulatory_region`` /
    ``regulatory_pathway`` fields. Do not add a value without first adding the
    concept to the ontology TTL.
    """

    EVIDENCE_DOC = "kb_evidence_doc"
    AIMODEL_CARD = "kb_aimodel_card"
    REGULATORY_DOC = "kb_regulatory_doc"
    PRODUCT_CARD = "kb_product_card"
    MANUFACTURER_CARD = "kb_manufacturer_card"

    # DEPRECATED (ADR-005): the Mongo use-case document path is retired to the
    # Postgres kb_use_cases spine. Retained transitionally (deprecate-and-defer,
    # ASHKBAPP-91); the ontology concept ash:dk-use-case carries owl:deprecated.
    # Remove this member together with that concept in the follow-up.
    USE_CASE = "kb_use_case"

    # Governance document types (ASHKBAPP-47)
    GOVERNANCE_DOC = "kb_governance_doc"
    GOVERNANCE_POLICY = "kb_governance_policy"
    GOVERNANCE_SOP = "kb_governance_sop"
    GOVERNANCE_WORK_PRODUCT = "kb_governance_work_product"
    GOVERNANCE_PROCESS = "kb_governance_process"
    GOVERNANCE_FRAMEWORK = "kb_governance_framework"
    GOVERNANCE_CONTROLS = "kb_governance_controls"

    # Fallback discriminator for uncategorized kb_documents (ASHKBAPP-91).
    GENERAL = "kb_general"


class RegulatoryRegion(str, Enum):
    """Regulatory jurisdiction of a regulatory document (the regulator axis).

    Single-sourced from ontology ``ash:RegulatoryRegionScheme`` (ASHKBAPP-91,
    ADR-002 Decision 5); values are the scheme's ``skos:notation``. Scopes a
    ``kb_regulatory_doc`` by jurisdiction (US->FDA, UK->MHRA, Canada->Health
    Canada, Australia->TGA, Japan->PMDA, China->NMPA). The ADR-002 CI guard
    enforces parity with the scheme.
    """

    USA = "USA"
    EU = "EU"
    UK = "UK"
    CA = "CA"
    AU = "AU"
    JP = "JP"
    CN = "CN"
    GLOBAL = "GLOBAL"


class RegulatoryPathway(str, Enum):
    """Regulatory submission / clearance pathway of a regulatory document.

    Single-sourced from ontology ``ash:RegulatoryPathwayScheme`` (ASHKBAPP-91,
    ADR-002 Decision 5); values are the scheme's ``skos:notation``. Broader than
    the FDA-API ``fda.enums.ClearanceType`` (adds Exempt and CE Mark for
    multi-jurisdiction scope); the two overlap and a future pass may relate them
    via SKOS mappings. The ADR-002 CI guard enforces parity with the scheme.
    """

    K510 = "510(k)"
    PMA = "PMA"
    DE_NOVO = "De Novo"
    HDE = "HDE"
    EUA = "EUA"
    EXEMPT = "Exempt"
    CE_MARK = "CE"


class ContentType(str, Enum):
    """Content type classifications within document types."""

    # Evidence types
    PEER_REVIEWED_PAPER = "peer_reviewed_paper"
    PREPRINT = "preprint"
    CLINICAL_TRIAL = "clinical_trial"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"

    # Regulatory types
    SUMMARY_510K = "510k_summary"
    PMA_SUMMARY = "pma_summary"
    DE_NOVO_SUMMARY = "de_novo_summary"

    # Model card types
    MODEL_CARD_V1 = "model_card_v1"

    # Profile types
    PRODUCT_PROFILE = "product_profile"
    COMPANY_PROFILE = "company_profile"
    CLINICAL_USE_CASE = "clinical_use_case"

    # Governance content types (ASHKBAPP-47)
    GOVERNANCE_POLICY_OVERVIEW = "governance_policy_overview"
    GOVERNANCE_POLICY_TEMPLATE = "governance_policy_template"
    GOVERNANCE_POLICY_BINDING = "governance_policy_binding"
    GOVERNANCE_SOP = "governance_sop"
    GOVERNANCE_WORK_PRODUCT = "governance_work_product"
    GOVERNANCE_WORK_PRODUCT_WIZARD = "governance_work_product_wizard"
    GOVERNANCE_PROCESS_AREA = "governance_process_area"
    GOVERNANCE_FRAMEWORK_OVERVIEW = "governance_framework_overview"
    GOVERNANCE_FRAMEWORK_GUIDE = "governance_framework_guide"
    GOVERNANCE_FRAMEWORK_REGISTRY = "governance_framework_registry"
    GOVERNANCE_CONTROLS_MAPPING = "governance_controls_mapping"
    GOVERNANCE_CONTROLS_REGISTRY = "governance_controls_registry"


# =============================================================================
# Tier 1: Metadata Object (Artifact Metadata)
# =============================================================================


class MetadataObjectBase(AshMaticsBaseModel):
    """
    Tier 1: Object metadata about the artifact/file itself.

    This contains information about the document as a stored artifact,
    not about its content. Used for tracking provenance, versioning,
    and storage management.
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the document was first created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the document was last updated",
    )
    created_by: str = Field(
        default="system",
        description="User ID or 'system' for automated creation",
    )
    version: str = Field(
        default="1.0",
        description="Document version string",
    )

    # Storage information
    file_size_bytes: int | None = Field(
        None,
        description="Size of the source file in bytes",
    )
    storage_location: str | None = Field(
        None,
        description="URI to source file (e.g., s3://bucket/path/file.pdf)",
    )
    source_pdf_url: str | None = Field(
        None,
        description="Azure Blob URL to original PDF file for user download/viewing",
    )
    markdown_url: str | None = Field(
        None,
        description="Azure Blob URL to full parsed markdown (from Docling/parser) for source verification",
    )
    checksum_md5: str | None = Field(
        None,
        max_length=32,
        description="MD5 checksum of source file",
    )
    original_filename: str | None = Field(
        None,
        description="Original filename when uploaded",
    )

    # Processing information
    processing_pipeline: str | None = Field(
        None,
        description="Name and version of processing pipeline (e.g., 'grobid_v0.7.2')",
    )
    processing_completed_at: datetime | None = Field(
        None,
        description="When processing completed",
    )
    processing_errors: list[str] = Field(
        default_factory=list,
        description="Any errors encountered during processing",
    )


# =============================================================================
# Tier 2: Metadata Content (Content Classification)
# =============================================================================


class MetadataContentBase(AshMaticsBaseModel):
    """
    Tier 2: Content metadata for classification and search.

    This contains metadata about the document's content for indexing,
    filtering, and categorization. Extended by type-specific schemas.
    """

    document_type: DocumentType = Field(
        ...,
        description="Type of document (the kb_documents KIND discriminator)",
        json_schema_extra={"x_ontology_scheme": "ash:DocumentKindScheme"},
    )
    content_type: ContentType = Field(
        ...,
        description="Specific content type within the document type",
    )
    title: str = Field(
        ...,
        description="Document title",
    )
    language: str = Field(
        default="en",
        max_length=5,
        description="ISO 639-1 language code",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="List of tags for categorization",
    )
    clinical_domain: str | None = Field(
        None,
        description="Primary clinical domain (e.g., 'radiology', 'cardiology')",
    )
    abstract: str | None = Field(
        None,
        description="Brief summary or abstract",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords for search",
    )


# =============================================================================
# Tier 3: Content Components
# =============================================================================


class SectionBase(AshMaticsBaseModel):
    """
    Base schema for a document section.

    Sections form the hierarchical structure of document content,
    supporting nested subsections for complex documents.
    """

    title: str = Field(
        ...,
        description="Section title",
    )
    order: int = Field(
        ...,
        ge=1,
        description="Display order within parent (1-indexed)",
    )
    text: str | None = Field(
        None,
        description="Section text content",
    )
    subsections: dict[str, "SectionBase"] = Field(
        default_factory=dict,
        description="Nested subsections keyed by section_id",
    )


class FigureReference(AshMaticsBaseModel):
    """Reference to a figure within a document."""

    figure_id: str = Field(
        ...,
        description="Unique figure identifier (e.g., 'fig1')",
    )
    caption: str | None = Field(
        None,
        description="Figure caption",
    )
    image_url: str | None = Field(
        None,
        description="URI to figure image",
    )
    referenced_in_sections: list[str] = Field(
        default_factory=list,
        description="Section IDs where this figure is referenced",
    )


class TableReference(AshMaticsBaseModel):
    """Reference to a table within a document."""

    table_id: str = Field(
        ...,
        description="Unique table identifier (e.g., 'table1')",
    )
    caption: str | None = Field(
        None,
        description="Table caption",
    )
    data: list[dict[str, Any]] | None = Field(
        None,
        description="Table data as list of row dictionaries",
    )
    referenced_in_sections: list[str] = Field(
        default_factory=list,
        description="Section IDs where this table is referenced",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional table metadata (e.g., markdown, source format, classification)",
    )


class CitationReference(AshMaticsBaseModel):
    """Reference to a citation/bibliography entry."""

    ref_id: str = Field(
        ...,
        description="Unique reference identifier (e.g., 'ref1')",
    )
    citation: str = Field(
        ...,
        description="Formatted citation text",
    )
    doi: str | None = Field(
        None,
        description="DOI if available",
    )
    pubmed_id: str | None = Field(
        None,
        description="PubMed ID if available",
    )


class ContentBase(AshMaticsBaseModel):
    """
    Tier 3: Base schema for document content.

    Contains the actual document body with sections, figures, tables,
    and references. Extended by type-specific content schemas.
    """

    sections: dict[str, SectionBase] = Field(
        default_factory=dict,
        description="Document sections keyed by section_id (e.g., '1_introduction')",
    )
    figures: list[FigureReference] = Field(
        default_factory=list,
        description="Figures referenced in the document",
    )
    tables: list[TableReference] = Field(
        default_factory=list,
        description="Tables referenced in the document",
    )
    references: list[CitationReference] = Field(
        default_factory=list,
        description="Bibliography/citations",
    )


# =============================================================================
# Complete Document Base
# =============================================================================


class MongoDocumentBase(AshMaticsBaseModel):
    """
    Base schema for all MongoDB documents with three-tier structure.

    All kb_* collection documents extend this base, providing consistent
    structure for embeddings, search, and API responses.
    """

    id: str | None = Field(
        None,
        alias="_id",
        description="MongoDB document ID",
    )
    metadata_object: MetadataObjectBase = Field(
        default_factory=MetadataObjectBase,
        description="Tier 1: Artifact metadata",
    )
    metadata_content: MetadataContentBase = Field(
        ...,
        description="Tier 2: Content classification metadata",
    )
    content: ContentBase = Field(
        default_factory=ContentBase,
        description="Tier 3: Document body",
    )

    model_config = {"populate_by_name": True}


# =============================================================================
# Summary/Response Schemas
# =============================================================================


class DocumentSummaryBase(AshMaticsBaseModel):
    """
    Base summary schema for document listings and search results.

    Flattens key fields from the three-tier structure for efficient
    API responses without loading full content.
    """

    id: str = Field(
        ...,
        alias="_id",
        description="MongoDB document ID",
    )
    document_type: DocumentType = Field(
        ...,
        description="Type of document",
    )
    content_type: ContentType = Field(
        ...,
        description="Content type classification",
    )
    title: str = Field(
        ...,
        description="Document title",
    )
    clinical_domain: str | None = Field(
        None,
        description="Primary clinical domain",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Document tags",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
    )

    model_config = {"populate_by_name": True}

    @classmethod
    def from_document(cls, doc: MongoDocumentBase) -> "DocumentSummaryBase":
        """Create summary from full document."""
        return cls(
            _id=doc.id or "",
            document_type=doc.metadata_content.document_type,
            content_type=doc.metadata_content.content_type,
            title=doc.metadata_content.title,
            clinical_domain=doc.metadata_content.clinical_domain,
            tags=doc.metadata_content.tags,
            created_at=doc.metadata_object.created_at,
            updated_at=doc.metadata_object.updated_at,
        )
