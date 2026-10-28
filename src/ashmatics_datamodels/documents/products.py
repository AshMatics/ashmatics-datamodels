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
Product Card schemas for kb_product_cards collection.

Product profiles with regulatory status, integrated AI models,
clinical evidence, and technical specifications.

Reference: docs/Plans/DocumentDataModelSchema-Normalize-2025-11-15/
"""

from datetime import date
from typing import Any, Optional

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.documents.base import (
    ContentBase,
    ContentType,
    DocumentSummaryBase,
    DocumentType,
    MetadataContentBase,
    MetadataObjectBase,
    MongoDocumentBase,
    SectionBase,
)


# =============================================================================
# Product Card Nested Schemas
# =============================================================================


class FDAClearanceRef(AshMaticsBaseModel):
    """Reference to an FDA clearance."""

    k_number: str = Field(
        ...,
        description="510(k) number",
    )
    clearance_date: Optional[date] = Field(
        None,
        description="Clearance date",
    )
    indications: Optional[str] = Field(
        None,
        description="Cleared indications for use",
    )


class IntegratedModelRef(AshMaticsBaseModel):
    """Reference to an integrated AI model."""

    model_id: Optional[str] = Field(
        None,
        description="Reference to the kb_aisystem_card document whose model parts describe this model",
    )
    model_name: str = Field(
        ...,
        description="Model name",
    )
    version: Optional[str] = Field(
        None,
        description="Model version",
    )
    purpose: Optional[str] = Field(
        None,
        description="Purpose within the product",
    )


class EvidenceRef(AshMaticsBaseModel):
    """Reference to clinical evidence."""

    evidence_id: Optional[str] = Field(
        None,
        description="Reference to kb_evidence_docs document",
    )
    title: str = Field(
        ...,
        description="Evidence title",
    )
    publication: Optional[str] = Field(
        None,
        description="Publication venue and date",
    )


class SystemRequirements(AshMaticsBaseModel):
    """Technical system requirements."""

    input_format: Optional[str] = Field(
        None,
        description="Input format (e.g., 'DICOM')",
    )
    output_format: Optional[str] = Field(
        None,
        description="Output format (e.g., 'HL7 FHIR')",
    )
    integration: list[str] = Field(
        default_factory=list,
        description="Integration targets (e.g., ['PACS', 'RIS', 'EHR'])",
    )
    additional_requirements: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional technical requirements",
    )


# =============================================================================
# Product Card Sections
# =============================================================================


class ProductOverviewSection(SectionBase):
    """Product overview section."""

    title: str = Field(default="Product Overview", description="Section title")
    order: int = Field(default=1, description="Section order")
    description: Optional[str] = Field(
        None,
        description="Product description",
    )
    device_type: Optional[str] = Field(
        None,
        description="Device type (e.g., 'SaMD')",
    )
    deployment_model: Optional[str] = Field(
        None,
        description="Deployment model (e.g., 'cloud-based', 'on-premise')",
    )


class RegulatoryStatusSection(SectionBase):
    """Regulatory status section."""

    title: str = Field(default="Regulatory Status", description="Section title")
    order: int = Field(default=2, description="Section order")
    fda_clearances: list[FDAClearanceRef] = Field(
        default_factory=list,
        description="FDA clearances for this product",
    )


class AIModelsSection(SectionBase):
    """AI models section."""

    title: str = Field(default="AI Models", description="Section title")
    order: int = Field(default=3, description="Section order")
    integrated_models: list[IntegratedModelRef] = Field(
        default_factory=list,
        description="AI models integrated into the product",
    )


class ClinicalEvidenceSection(SectionBase):
    """Clinical evidence section."""

    title: str = Field(default="Clinical Evidence", description="Section title")
    order: int = Field(default=4, description="Section order")
    key_studies: list[EvidenceRef] = Field(
        default_factory=list,
        description="Key clinical studies",
    )


class TechnicalSpecsSection(SectionBase):
    """Technical specifications section."""

    title: str = Field(default="Technical Specifications", description="Section title")
    order: int = Field(default=5, description="Section order")
    system_requirements: Optional[SystemRequirements] = Field(
        None,
        description="System requirements",
    )


# =============================================================================
# Product Card Metadata Content
# =============================================================================


class ProductCardMetadataContent(MetadataContentBase):
    """
    Metadata content specific to product cards.
    """

    document_type: DocumentType = Field(
        default=DocumentType.PRODUCT_CARD,
        description="Always 'kb_product_card'",
    )
    content_type: ContentType = Field(
        default=ContentType.PRODUCT_PROFILE,
        description="Product profile type",
    )

    # Product identification
    product_name: str = Field(
        ...,
        description="Product name",
    )
    manufacturer: str = Field(
        ...,
        description="Manufacturer name",
    )
    fda_status: Optional[str] = Field(
        None,
        description="FDA status (e.g., 'cleared', 'approved', 'pending')",
    )
    k_numbers: list[str] = Field(
        default_factory=list,
        description="Associated 510(k) numbers",
    )


# =============================================================================
# Product Card Content
# =============================================================================


class ProductCardContent(ContentBase):
    """
    Content structure for product cards.
    """

    sections: dict[str, SectionBase] = Field(
        default_factory=lambda: {
            "product_overview": ProductOverviewSection(
                title="Product Overview", order=1
            ),
            "regulatory_status": RegulatoryStatusSection(
                title="Regulatory Status", order=2
            ),
            "ai_models": AIModelsSection(title="AI Models", order=3),
            "clinical_evidence": ClinicalEvidenceSection(
                title="Clinical Evidence", order=4
            ),
            "technical_specifications": TechnicalSpecsSection(
                title="Technical Specifications", order=5
            ),
        },
        description="Product card sections",
    )


# =============================================================================
# Complete Product Card Document
# =============================================================================


class ProductCardDocument(MongoDocumentBase):
    """
    Complete product card with three-tier structure.

    Used for kb_product_cards MongoDB collection.
    """

    metadata_object: MetadataObjectBase = Field(
        default_factory=MetadataObjectBase,
        description="Artifact metadata",
    )
    metadata_content: ProductCardMetadataContent = Field(
        ...,
        description="Product card metadata",
    )
    content: ProductCardContent = Field(
        default_factory=ProductCardContent,
        description="Product card content",
    )


class ProductCardDocumentCreate(MongoDocumentBase):
    """Schema for creating a new product card."""

    metadata_content: ProductCardMetadataContent = Field(
        ...,
        description="Required product card metadata",
    )
    content: ProductCardContent = Field(
        default_factory=ProductCardContent,
        description="Product card content",
    )


# =============================================================================
# Product Card Summary
# =============================================================================


class ProductCardSummary(DocumentSummaryBase):
    """
    Summary view for product cards in listings.
    """

    document_type: DocumentType = Field(
        default=DocumentType.PRODUCT_CARD,
        description="Always kb_product_card",
    )

    # Product-specific summary fields
    product_name: str = Field(
        ...,
        description="Product name",
    )
    manufacturer: str = Field(
        ...,
        description="Manufacturer name",
    )
    fda_status: Optional[str] = Field(
        None,
        description="FDA status",
    )
    k_numbers: list[str] = Field(
        default_factory=list,
        description="510(k) numbers",
    )

    @classmethod
    def from_document(cls, doc: ProductCardDocument) -> "ProductCardSummary":
        """Create summary from full product card."""
        return cls(
            _id=doc.id or "",
            document_type=doc.metadata_content.document_type,
            content_type=doc.metadata_content.content_type,
            title=doc.metadata_content.title,
            clinical_domain=doc.metadata_content.clinical_domain,
            tags=doc.metadata_content.tags,
            created_at=doc.metadata_object.created_at,
            updated_at=doc.metadata_object.updated_at,
            product_name=doc.metadata_content.product_name,
            manufacturer=doc.metadata_content.manufacturer,
            fda_status=doc.metadata_content.fda_status,
            k_numbers=doc.metadata_content.k_numbers,
        )
