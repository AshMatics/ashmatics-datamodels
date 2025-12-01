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
MongoDB document schemas with standardized three-tier structure.

All kb_* MongoDB collections follow this pattern:
- Tier 1: metadata_object - Artifact/file metadata
- Tier 2: metadata_content - Content classification metadata
- Tier 3: content - Actual document body with sections

This module provides Pydantic models for:
- kb_evidence_docs: Peer-reviewed papers and clinical evidence
- kb_regulatory_docs: FDA 510(k), PMA, De Novo summaries
- kb_aimodel_cards: AI model cards with architecture and performance
- kb_product_cards: Product profiles with regulatory status
- kb_manufacturer_cards: Company profiles and portfolios
- kb_use_cases: Clinical use cases with applicable products
- kb_governance_*: Clinical AI Governance Framework artifacts (ASHKBAPP-47)
  - PolicyDocument: Policy domain documents (overview, template, binding)
  - SOPDocument: Standard Operating Procedures
  - WorkProductDocument: Work Product templates and guides
  - ProcessDocument: Process area base documentation
  - FrameworkDocument: Framework-level documentation
  - ControlsDocument: Controls and validation tools

Reference: docs/Plans/DocumentDataModelSchema-Normalize-2025-11-15/
"""

# Base schemas
from ashmatics_datamodels.documents.base import (
    CitationReference,
    ContentBase,
    ContentType,
    DocumentSummaryBase,
    DocumentType,
    FigureReference,
    MetadataContentBase,
    MetadataObjectBase,
    MongoDocumentBase,
    SectionBase,
    TableReference,
)

# Evidence documents
from ashmatics_datamodels.documents.evidence import (
    EvidenceContent,
    EvidenceDocument,
    EvidenceDocumentCreate,
    EvidenceMetadataContent,
    EvidenceSummary,
)
from ashmatics_datamodels.documents.governance import (
    ControlsDocument,
    EmbeddingsMeta,
    FrameworkDocument,
    GovernanceCitation,
    GovernanceContent,
    GovernanceDocument,
    GovernanceDocumentBase,
    GovernanceDocumentCreate,
    GovernanceMetadataContent,
    GovernancePlaceholder,
    GovernanceSection,
    GovernanceSummary,
    PolicyBinding,
    PolicyDocument,
    ProcessDocument,
    SOPDocument,
    TraceabilityInfo,
    WorkProductDocument,
)

# Governance documents (ASHKBAPP-47)
from ashmatics_datamodels.documents.governance_enums import (
    ContentFormat,
    DomainType,
    GovernanceArtifactType,
    GovernanceCategory,
    GovernanceContentType,
    GovernanceSubcategory,
    ProcessDomainCode,
)

# Manufacturer cards
from ashmatics_datamodels.documents.manufacturers import (
    ClearanceRef,
    ManufacturerCardContent,
    ManufacturerCardDocument,
    ManufacturerCardDocumentCreate,
    ManufacturerCardMetadataContent,
    ManufacturerCardSummary,
    ProductRef,
)

# AI Model cards
from ashmatics_datamodels.documents.models import (
    DataSplits,
    ExternalResources,
    InputSpecs,
    ModelCardContent,
    ModelCardDocument,
    ModelCardDocumentCreate,
    ModelCardMetadataContent,
    ModelCardSummary,
    OutputSpecs,
    PerformanceMetrics,
)

# Product cards
from ashmatics_datamodels.documents.products import (
    EvidenceRef,
    FDAClearanceRef,
    IntegratedModelRef,
    ProductCardContent,
    ProductCardDocument,
    ProductCardDocumentCreate,
    ProductCardMetadataContent,
    ProductCardSummary,
    SystemRequirements,
)

# Regulatory documents
from ashmatics_datamodels.documents.regulatory import (
    # Phase 2D models
    DatasetCharacteristics,
    # Phase 2E enums
    MetricType,
    PatientDemographics,
    # Phase 2E models
    PerformanceMetric,
    PerformanceTestResults,
    PredicateDeviceInfo,
    RegulatoryContent,
    RegulatoryDocument,
    RegulatoryDocumentCreate,
    RegulatoryMetadataContent,
    RegulatorySummary,
    StructuredIndication,
    StudyType,
    TestDataset,
    TrainingDataCharacteristics,
    ValidationStudy,
)

# Use cases
from ashmatics_datamodels.documents.use_cases import (
    ApplicableProductRef,
    SupportingEvidenceRef,
    UseCaseContent,
    UseCaseDocument,
    UseCaseDocumentCreate,
    UseCaseMetadataContent,
    UseCaseSummary,
)

__all__ = [
    # Enums
    "DocumentType",
    "ContentType",
    # Base schemas
    "MetadataObjectBase",
    "MetadataContentBase",
    "SectionBase",
    "ContentBase",
    "MongoDocumentBase",
    "DocumentSummaryBase",
    "FigureReference",
    "TableReference",
    "CitationReference",
    # Evidence
    "EvidenceMetadataContent",
    "EvidenceContent",
    "EvidenceDocument",
    "EvidenceDocumentCreate",
    "EvidenceSummary",
    # Regulatory
    "RegulatoryMetadataContent",
    "RegulatoryContent",
    "RegulatoryDocument",
    "RegulatoryDocumentCreate",
    "RegulatorySummary",
    "StructuredIndication",
    "PredicateDeviceInfo",
    "PerformanceTestResults",
    # Phase 2E Performance Data Models
    "StudyType",
    "MetricType",
    "PerformanceMetric",
    "TestDataset",
    "ValidationStudy",
    # Phase 2D Training Data Models
    "TrainingDataCharacteristics",
    "DatasetCharacteristics",
    "PatientDemographics",
    # Model Cards
    "ModelCardMetadataContent",
    "ModelCardContent",
    "ModelCardDocument",
    "ModelCardDocumentCreate",
    "ModelCardSummary",
    "InputSpecs",
    "OutputSpecs",
    "DataSplits",
    "PerformanceMetrics",
    "ExternalResources",
    # Product Cards
    "ProductCardMetadataContent",
    "ProductCardContent",
    "ProductCardDocument",
    "ProductCardDocumentCreate",
    "ProductCardSummary",
    "FDAClearanceRef",
    "IntegratedModelRef",
    "EvidenceRef",
    "SystemRequirements",
    # Manufacturer Cards
    "ManufacturerCardMetadataContent",
    "ManufacturerCardContent",
    "ManufacturerCardDocument",
    "ManufacturerCardDocumentCreate",
    "ManufacturerCardSummary",
    "ProductRef",
    "ClearanceRef",
    # Use Cases
    "UseCaseMetadataContent",
    "UseCaseContent",
    "UseCaseDocument",
    "UseCaseDocumentCreate",
    "UseCaseSummary",
    "ApplicableProductRef",
    "SupportingEvidenceRef",
    # Governance Enums (ASHKBAPP-47)
    "ProcessDomainCode",
    "GovernanceCategory",
    "GovernanceSubcategory",
    "DomainType",
    "ContentFormat",
    "GovernanceContentType",
    "GovernanceArtifactType",
    # Governance Content Components
    "GovernancePlaceholder",
    "PolicyBinding",
    "TraceabilityInfo",
    "GovernanceCitation",
    "EmbeddingsMeta",
    "GovernanceSection",
    # Governance Documents
    "GovernanceMetadataContent",
    "GovernanceContent",
    "GovernanceDocumentBase",
    "GovernanceDocument",
    "GovernanceDocumentCreate",
    "GovernanceSummary",
    "PolicyDocument",
    "SOPDocument",
    "WorkProductDocument",
    "ProcessDocument",
    "FrameworkDocument",
    "ControlsDocument",
]
