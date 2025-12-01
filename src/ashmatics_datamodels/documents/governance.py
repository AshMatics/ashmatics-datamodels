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
Governance document schemas for Clinical AI Governance Framework.

Provides Pydantic models for governance artifacts stored in MongoDB:
- PolicyDocument: Policy domain documents (overview, template, binding)
- SOPDocument: Standard Operating Procedures
- WorkProductDocument: Work Product templates and guides
- ProcessDocument: Process area base documentation
- FrameworkDocument: Framework-level documentation (overview, guide, registry)

These models follow the three-tier structure:
- Tier 1: metadata_object - Artifact/file metadata
- Tier 2: metadata_content - Content classification metadata
- Tier 3: content - Actual document body with sections

Reference: ASHKBAPP-47 - Refactor CAI Framework to Common Datamodels
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.documents.base import (
    ContentBase,
    DocumentSummaryBase,
    MetadataContentBase,
    MetadataObjectBase,
    MongoDocumentBase,
)
from ashmatics_datamodels.documents.governance_enums import (
    ContentFormat,
    DomainType,
    GovernanceArtifactType,
    GovernanceCategory,
    GovernanceContentType,
    GovernanceSubcategory,
    ProcessDomainCode,
)

# =============================================================================
# Governance-Specific Content Components
# =============================================================================


class GovernancePlaceholder(AshMaticsBaseModel):
    """
    Template placeholder extracted from governance content.

    Placeholders are tokens like {{PLACEHOLDER_NAME}} that require
    runtime substitution when generating documents.
    """

    token: str = Field(
        ...,
        description="Full placeholder token (e.g., '{{PLACEHOLDER_NAME}}')",
    )
    name: str = Field(
        ...,
        description="Extracted placeholder name without braces",
    )
    required: bool = Field(
        default=False,
        description="True if placeholder is required (uppercase convention)",
    )
    context: str = Field(
        default="",
        max_length=200,
        description="Surrounding context (up to 200 chars total)",
    )


class PolicyBinding(AshMaticsBaseModel):
    """
    Policy or process binding reference extracted from content.

    Bindings link governance artifacts to specific policies or processes
    (e.g., "Policy PV-01", "Process EF-09").
    """

    binding_type: Literal["policy", "process"] = Field(
        ...,
        description="Type of binding (policy or process)",
    )
    code: str = Field(
        ...,
        description="Binding code (e.g., 'PV-01', 'EF-09')",
    )
    reference: str = Field(
        ...,
        description="Full reference text as found in document",
    )
    context: str = Field(
        default="",
        max_length=200,
        description="Surrounding context for the binding",
    )


class TraceabilityInfo(AshMaticsBaseModel):
    """
    Traceability metadata for process artifacts.

    Links artifacts to process outputs and dependencies for
    governance audit trails.
    """

    process_outputs: list[str] = Field(
        default_factory=list,
        description="Output IDs produced by this artifact",
    )
    contributes_to: list[str] = Field(
        default_factory=list,
        description="Process outputs this artifact contributes to",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Artifacts or outputs this depends on",
    )
    traceability_file: str | None = Field(
        None,
        description="Path to dedicated traceability JSON file if applicable",
    )


class GovernanceCitation(AshMaticsBaseModel):
    """
    Citation or reference extracted from governance content.

    Captures links to standards, regulations, and external references.
    """

    text: str = Field(
        ...,
        description="Citation text or link text",
    )
    url: str | None = Field(
        None,
        description="URL if available",
    )
    citation_type: Literal["link", "reference", "doi", "isbn", "standard"] = Field(
        default="reference",
        description="Type of citation",
    )


class EmbeddingsMeta(AshMaticsBaseModel):
    """
    Metadata for document embeddings (for AI agent retrieval).
    """

    needs_embedding: bool = Field(
        default=True,
        description="Whether this document needs embedding generation",
    )
    embedding_model: str | None = Field(
        None,
        description="Model used for embedding (e.g., 'text-embedding-ada-002')",
    )
    embedding_vector: list[float] | None = Field(
        None,
        description="Embedding vector if pre-computed",
    )
    embedded_at: datetime | None = Field(
        None,
        description="When embedding was generated",
    )


# =============================================================================
# Governance-Specific Section Structure
# =============================================================================


class GovernanceSection(AshMaticsBaseModel):
    """
    Section structure for governance documents.

    Extends base section with governance-specific fields like
    anchors for navigation and hierarchical level.
    """

    level: int = Field(
        default=1,
        ge=1,
        le=6,
        description="Heading level (1-6, corresponds to H1-H6)",
    )
    title: str = Field(
        ...,
        description="Section title",
    )
    anchor: str = Field(
        default="",
        description="URL anchor for navigation (normalized title)",
    )
    content: str = Field(
        default="",
        description="Section body content (markdown or plain text)",
    )
    subsections: list["GovernanceSection"] = Field(
        default_factory=list,
        description="Nested subsections",
    )


# Enable forward reference resolution
GovernanceSection.model_rebuild()


# =============================================================================
# Governance Metadata Content (Tier 2)
# =============================================================================


class GovernanceMetadataContent(MetadataContentBase):
    """
    Metadata content specific to governance artifacts.

    Extends base metadata with CAI framework-specific fields including
    4-tier categorization, domain classification, and source tracking.
    """

    # Override document_type to use string for flexibility
    # (governance types not in base DocumentType enum initially)
    document_type: str = Field(
        default="kb_governance_doc",
        description="Document type for MongoDB collection routing",
    )
    content_type: str = Field(
        default="governance_artifact",
        description="Content type classification",
    )

    # Framework versioning
    framework_version: str = Field(
        default="0.1.0",
        description="Semantic version of the governance framework",
    )
    artifact_id: str = Field(
        ...,
        description="Unique cross-database identifier for the artifact",
    )

    # 4-Tier categorization (from CAI framework)
    content_category: GovernanceCategory = Field(
        ...,
        description="Tier 1: Primary content category",
    )
    subcategory: GovernanceSubcategory = Field(
        ...,
        description="Tier 2: Detailed subcategory",
    )
    subcategory_label: str = Field(
        default="",
        description="API-friendly label for filtering (e.g., 'sop', 'wp')",
    )
    process_domain_code: ProcessDomainCode | None = Field(
        None,
        description="Tier 3: Process domain code (PV, SA, MON, etc.)",
    )
    content_format: ContentFormat = Field(
        default=ContentFormat.MARKDOWN,
        description="Tier 4: Source file format",
    )

    # Domain classification
    domain_type: DomainType = Field(
        default=DomainType.GOVERNANCE,
        description="Domain type (process, policy, controls, governance)",
    )
    domain_code: str = Field(
        default="",
        description="2-3 letter domain code",
    )
    domain_name: str = Field(
        default="",
        description="Human-readable domain name",
    )
    control_type: str | None = Field(
        None,
        description="For controls: base_mapping, iso_mapping, tools_registry, general",
    )

    # Source tracking
    relative_path: str = Field(
        ...,
        description="File path relative to framework repository root",
    )
    storage_location: str | None = Field(
        None,
        description="Azure Blob Storage URL for source file",
    )
    content_hash: str = Field(
        default="",
        description="SHA-256 hash for content integrity verification",
    )


# =============================================================================
# Governance Content (Tier 3)
# =============================================================================


class GovernanceContent(ContentBase):
    """
    Content structure for governance artifacts.

    Extends base content with governance-specific fields including
    placeholders, policy bindings, traceability, and normative references.
    """

    # Override sections with governance-specific structure
    governance_sections: list[GovernanceSection] = Field(
        default_factory=list,
        description="Hierarchical sections with governance-specific structure",
    )

    # Governance-specific content
    placeholders: list[GovernancePlaceholder] = Field(
        default_factory=list,
        description="Template placeholders extracted from content",
    )
    policy_bindings: list[PolicyBinding] = Field(
        default_factory=list,
        description="Policy and process binding references",
    )
    traceability: TraceabilityInfo | None = Field(
        None,
        description="Traceability metadata linking to process outputs",
    )
    citations: list[GovernanceCitation] = Field(
        default_factory=list,
        description="Citations and external references",
    )
    normative_refs: list[str] = Field(
        default_factory=list,
        description="Normative references (ISO, NIST, FDA, HIPAA, GDPR, SOX)",
    )
    outputs_contribute_to: list[str] = Field(
        default_factory=list,
        description="Process outputs this artifact contributes to",
    )

    # Token estimation for AI context management
    tokens_required: int = Field(
        default=0,
        ge=0,
        description="Estimated token count for AI context (~4 chars per token)",
    )

    # Embedding support
    embeddings_meta: EmbeddingsMeta | None = Field(
        None,
        description="Embedding metadata for AI retrieval",
    )

    # Original source metadata
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Original markdown frontmatter or JSON metadata",
    )

    # Content type indicator (from mongo_compiler)
    governance_content_type: GovernanceContentType = Field(
        default=GovernanceContentType.COMPILED_MARKDOWN,
        description="Type of stored content (compiled_markdown, json_native, yaml_native)",
    )


# =============================================================================
# Complete Governance Documents
# =============================================================================


class GovernanceDocumentBase(MongoDocumentBase):
    """
    Base class for all governance documents.

    Provides common structure for the three-tier MongoDB document
    with governance-specific metadata and content.
    """

    metadata_object: MetadataObjectBase = Field(
        default_factory=MetadataObjectBase,
        description="Tier 1: Artifact metadata",
    )
    metadata_content: GovernanceMetadataContent = Field(
        ...,
        description="Tier 2: Governance-specific metadata",
    )
    content: GovernanceContent = Field(
        default_factory=GovernanceContent,
        description="Tier 3: Governance content with sections",
    )

    # Framework schema version for compatibility
    framework_schema: str = Field(
        default="v1",
        alias="_framework_schema",
        description="Schema version for forward compatibility",
    )
    stored_at: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC),
        alias="_stored_at",
        description="When document was stored in MongoDB",
    )
    source: str = Field(
        default="framework_content_importer",
        alias="_source",
        description="Source system that created this document",
    )


class PolicyDocument(GovernanceDocumentBase):
    """
    Policy domain document (overview, template, binding, glue).

    Used for policy-related governance artifacts including domain overviews,
    policy templates, and binding definitions.
    """

    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.POLICY,
        description="Artifact type identifier",
    )
    policy_type: Literal["overview", "template", "binding", "glue"] = Field(
        default="overview",
        description="Type of policy document",
    )
    applicable_domains: list[str] = Field(
        default_factory=list,
        description="Process domains this policy applies to",
    )


class SOPDocument(GovernanceDocumentBase):
    """
    Standard Operating Procedure document.

    Used for SOP-XX-YY formatted documents that define operational
    procedures within process domains.
    """

    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.SOP,
        description="Artifact type identifier",
    )
    sop_code: str = Field(
        default="",
        description="SOP code (e.g., 'SOP-OVR-03')",
    )
    process_area: str = Field(
        default="",
        description="Parent process area name",
    )
    version_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Version history entries",
    )


class WorkProductDocument(GovernanceDocumentBase):
    """
    Work Product template or guide document.

    Used for WP-XX-YY formatted documents including templates,
    checklists, and wizard guides.
    """

    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.WORK_PRODUCT,
        description="Artifact type identifier",
    )
    wp_code: str = Field(
        default="",
        description="Work product code (e.g., 'WP-RM-02')",
    )
    output_type: str = Field(
        default="document",
        description="Output type (document, checklist, log, template)",
    )
    is_wizard: bool = Field(
        default=False,
        description="True for wizard guide documents",
    )
    contributes_to_outputs: list[str] = Field(
        default_factory=list,
        description="Process outputs this work product contributes to",
    )


class ProcessDocument(GovernanceDocumentBase):
    """
    Process area base documentation.

    Used for AshmaticsAIGov-Area*.md style documents that define
    process areas within the governance framework.
    """

    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.PROCESS,
        description="Artifact type identifier",
    )
    process_area_code: str = Field(
        default="",
        description="Process area code (e.g., 'OVR', 'RM')",
    )
    process_area_name: str = Field(
        default="",
        description="Full process area name",
    )
    process_area_number: int | None = Field(
        None,
        ge=1,
        description="Process area number (e.g., 5 for Area 5)",
    )
    related_sops: list[str] = Field(
        default_factory=list,
        description="Related SOP codes",
    )
    related_wps: list[str] = Field(
        default_factory=list,
        description="Related work product codes",
    )


class FrameworkDocument(GovernanceDocumentBase):
    """
    Framework-level documentation.

    Used for top-level framework documents including overviews,
    implementation guides, registries, and architecture docs.
    """

    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.FRAMEWORK,
        description="Artifact type identifier",
    )
    framework_component: str = Field(
        default="overview",
        description="Component type (overview, implementation_guide, registry, architecture)",
    )


class ControlsDocument(GovernanceDocumentBase):
    """
    Controls and validation tools document.

    Used for control frameworks, ISO mappings, and tool registries.
    """

    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.CONTROLS,
        description="Artifact type identifier",
    )
    control_framework: str = Field(
        default="",
        description="Control framework name (e.g., 'ISO-42001')",
    )
    mapping_type: str | None = Field(
        None,
        description="Type of mapping (iso_mapping, base_mapping, tools_registry)",
    )


# Union type for any governance document
GovernanceDocument = (
    PolicyDocument
    | SOPDocument
    | WorkProductDocument
    | ProcessDocument
    | FrameworkDocument
    | ControlsDocument
)


# =============================================================================
# Create Schemas
# =============================================================================


class GovernanceDocumentCreate(AshMaticsBaseModel):
    """Schema for creating a new governance document."""

    metadata_content: GovernanceMetadataContent = Field(
        ...,
        description="Required governance metadata",
    )
    content: GovernanceContent = Field(
        default_factory=GovernanceContent,
        description="Governance content",
    )
    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.FRAMEWORK,
        description="Type of governance artifact",
    )


# =============================================================================
# Summary Schemas
# =============================================================================


class GovernanceSummary(DocumentSummaryBase):
    """
    Summary view for governance documents in listings.

    Flattens key governance metadata for search results and API responses.
    """

    document_type: str = Field(
        default="kb_governance_doc",
        description="Document type",
    )
    # Override content_type to accept string (governance uses different types)
    content_type: str = Field(
        default="governance_artifact",
        description="Content type classification",
    )

    # Governance-specific summary fields
    artifact_type: GovernanceArtifactType = Field(
        default=GovernanceArtifactType.FRAMEWORK,
        description="Type of governance artifact",
    )
    framework_version: str = Field(
        default="",
        description="Framework version",
    )
    artifact_id: str = Field(
        default="",
        description="Unique artifact identifier",
    )
    content_category: GovernanceCategory | None = Field(
        None,
        description="Primary content category",
    )
    subcategory: GovernanceSubcategory | None = Field(
        None,
        description="Detailed subcategory",
    )
    process_domain_code: ProcessDomainCode | None = Field(
        None,
        description="Process domain code",
    )
    domain_name: str = Field(
        default="",
        description="Domain name",
    )
    relative_path: str = Field(
        default="",
        description="File path in framework repo",
    )
    tokens_required: int = Field(
        default=0,
        description="Estimated token count",
    )

    @classmethod
    def from_document(cls, doc: GovernanceDocumentBase) -> "GovernanceSummary":
        """Create summary from full governance document."""
        return cls(
            _id=doc.id or "",
            document_type=doc.metadata_content.document_type,
            content_type=doc.metadata_content.content_type,
            title=doc.metadata_content.title,
            clinical_domain=doc.metadata_content.clinical_domain,
            tags=doc.metadata_content.tags,
            created_at=doc.metadata_object.created_at,
            updated_at=doc.metadata_object.updated_at,
            artifact_type=getattr(doc, "artifact_type", GovernanceArtifactType.FRAMEWORK),
            framework_version=doc.metadata_content.framework_version,
            artifact_id=doc.metadata_content.artifact_id,
            content_category=doc.metadata_content.content_category,
            subcategory=doc.metadata_content.subcategory,
            process_domain_code=doc.metadata_content.process_domain_code,
            domain_name=doc.metadata_content.domain_name,
            relative_path=doc.metadata_content.relative_path,
            tokens_required=doc.content.tokens_required,
        )
