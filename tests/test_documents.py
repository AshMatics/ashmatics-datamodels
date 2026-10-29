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

"""Tests for MongoDB document schemas with three-tier structure."""

from datetime import date, datetime

import pytest

from ashmatics_datamodels.documents import (
    ContentType,
    DocumentType,
    EvidenceDocument,
    EvidenceMetadataContent,
    EvidenceSummary,
    ManufacturerCardDocument,
    ManufacturerCardMetadataContent,
    MetadataObjectBase,
    PredicateDeviceInfo,
    ProductCardDocument,
    ProductCardMetadataContent,
    RegulatoryDocument,
    RegulatoryMetadataContent,
    SectionBase,
    UseCaseDocument,
    UseCaseMetadataContent,
)


class TestMetadataObjectBase:
    """Tests for Tier 1: Metadata Object."""

    def test_default_values(self):
        """Test default metadata object creation."""
        meta = MetadataObjectBase()
        assert meta.created_by == "system"
        assert meta.version == "1.0"
        assert isinstance(meta.created_at, datetime)
        assert meta.processing_errors == []

    def test_with_storage_info(self):
        """Test metadata with storage information."""
        meta = MetadataObjectBase(
            storage_location="s3://kb-evidence/papers/test.pdf",
            file_size_bytes=1024000,
            checksum_md5="abc123def456",
            original_filename="test_paper.pdf",
            processing_pipeline="grobid_v0.7.2",
        )
        assert meta.storage_location == "s3://kb-evidence/papers/test.pdf"
        assert meta.file_size_bytes == 1024000
        assert meta.checksum_md5 == "abc123def456"


class TestSectionBase:
    """Tests for document sections."""

    def test_basic_section(self):
        """Test basic section creation."""
        section = SectionBase(
            title="Introduction",
            order=1,
            text="This is the introduction text.",
        )
        assert section.title == "Introduction"
        assert section.order == 1
        assert section.subsections == {}

    def test_nested_subsections(self):
        """Test section with subsections."""
        section = SectionBase(
            title="Methods",
            order=2,
            text="Methods overview",
            subsections={
                "2.1_study_design": SectionBase(
                    title="Study Design", order=1, text="Study design details"
                ),
                "2.2_data_collection": SectionBase(
                    title="Data Collection", order=2, text="Data collection details"
                ),
            },
        )
        assert len(section.subsections) == 2
        assert section.subsections["2.1_study_design"].title == "Study Design"


class TestEvidenceDocument:
    """Tests for kb_evidence_docs schemas."""

    def test_evidence_document_creation(self):
        """Test creating a complete evidence document."""
        doc = EvidenceDocument(
            _id="test-evidence-123",
            metadata_content=EvidenceMetadataContent(
                document_type=DocumentType.EVIDENCE_DOC,
                content_type=ContentType.PEER_REVIEWED_PAPER,
                title="Deep Learning for Chest X-ray Analysis",
                clinical_domain="radiology",
                authors=["Jane Smith", "John Doe"],
                journal="Radiology: AI",
                doi="10.1148/ryai.2024123456",
                publication_date=date(2024, 3, 15),
                anatomical_region="chest",
                pathology_focus=["pneumonia", "pleural_effusion"],
            ),
        )
        assert doc.id == "test-evidence-123"
        assert doc.metadata_content.title == "Deep Learning for Chest X-ray Analysis"
        assert doc.metadata_content.authors == ["Jane Smith", "John Doe"]
        assert doc.metadata_content.doi == "10.1148/ryai.2024123456"

    def test_evidence_summary_from_document(self):
        """Test creating summary from full document."""
        doc = EvidenceDocument(
            _id="test-evidence-456",
            metadata_content=EvidenceMetadataContent(
                document_type=DocumentType.EVIDENCE_DOC,
                content_type=ContentType.PEER_REVIEWED_PAPER,
                title="AI in Radiology",
                clinical_domain="radiology",
                authors=["Test Author"],
                journal="Test Journal",
                abstract="This is a test abstract.",
            ),
        )
        summary = EvidenceSummary.from_document(doc)
        assert summary.id == "test-evidence-456"
        assert summary.title == "AI in Radiology"
        assert summary.authors == ["Test Author"]
        assert summary.journal == "Test Journal"


class TestRegulatoryDocument:
    """Tests for kb_regulatory_docs schemas."""

    def test_regulatory_document_creation(self):
        """Test creating a 510(k) regulatory document."""
        doc = RegulatoryDocument(
            _id="test-regulatory-123",
            metadata_content=RegulatoryMetadataContent(
                document_type=DocumentType.REGULATORY_DOC,
                content_type=ContentType.SUMMARY_510K,
                title="AI-Chest Scanner 510(k) Summary",
                k_number="K240001",
                clearance_date=date(2024, 8, 15),
                applicant="Medical AI Corp",
                device_name="AI-Chest Scanner",
                device_class="II",
                product_code="MYN",
                clinical_domain="radiology",
            ),
        )
        assert doc.metadata_content.k_number == "K240001"
        assert doc.metadata_content.device_class == "II"
        assert doc.metadata_content.product_code == "MYN"

    def test_predicate_device_info(self):
        """Test predicate device schema."""
        predicate = PredicateDeviceInfo(
            k_number="K190123",
            device_name="ChestView AI",
            manufacturer="Competing AI Inc",
            comparison_summary="Similar intended use and technological characteristics",
        )
        assert predicate.k_number == "K190123"
        assert predicate.manufacturer == "Competing AI Inc"


class TestProductCardDocument:
    """Tests for kb_product_cards schemas."""

    def test_product_card_creation(self):
        """Test creating a product card."""
        doc = ProductCardDocument(
            _id="test-product-123",
            metadata_content=ProductCardMetadataContent(
                document_type=DocumentType.PRODUCT_CARD,
                content_type=ContentType.PRODUCT_PROFILE,
                title="AI-Chest Scanner Product Profile",
                product_name="AI-Chest Scanner",
                manufacturer="Medical AI Corp",
                fda_status="cleared",
                k_numbers=["K240001"],
                clinical_domain="radiology",
            ),
        )
        assert doc.metadata_content.product_name == "AI-Chest Scanner"
        assert doc.metadata_content.fda_status == "cleared"
        assert "K240001" in doc.metadata_content.k_numbers


class TestManufacturerCardDocument:
    """Tests for kb_manufacturer_cards schemas."""

    def test_manufacturer_card_creation(self):
        """Test creating a manufacturer card."""
        doc = ManufacturerCardDocument(
            _id="test-manufacturer-123",
            metadata_content=ManufacturerCardMetadataContent(
                document_type=DocumentType.MANUFACTURER_CARD,
                content_type=ContentType.COMPANY_PROFILE,
                title="Medical AI Corp Company Profile",
                company_name="Medical AI Corp",
                headquarters="San Francisco, CA",
                founded="2018",
                clinical_domain="radiology",
            ),
        )
        assert doc.metadata_content.company_name == "Medical AI Corp"
        assert doc.metadata_content.headquarters == "San Francisco, CA"
        assert doc.metadata_content.founded == "2018"


class TestUseCaseDocument:
    """Tests for kb_use_cases schemas."""

    def test_use_case_creation(self):
        """Test creating a use case document."""
        doc = UseCaseDocument(
            _id="test-usecase-123",
            metadata_content=UseCaseMetadataContent(
                document_type=DocumentType.USE_CASE,
                content_type=ContentType.CLINICAL_USE_CASE,
                title="Chest X-ray Pneumonia Detection in ED",
                clinical_domain="radiology",
                clinical_specialty="Emergency Medicine",
                anatomical_region="chest",
                pathology=["pneumonia"],
            ),
        )
        assert doc.metadata_content.clinical_specialty == "Emergency Medicine"
        assert doc.metadata_content.anatomical_region == "chest"
        assert "pneumonia" in doc.metadata_content.pathology


class TestDocumentSerialization:
    """Tests for document JSON serialization."""

    def test_evidence_to_json(self):
        """Test evidence document JSON export."""
        doc = EvidenceDocument(
            _id="json-test-123",
            metadata_content=EvidenceMetadataContent(
                document_type=DocumentType.EVIDENCE_DOC,
                content_type=ContentType.PEER_REVIEWED_PAPER,
                title="Test Paper",
                authors=["Author One"],
            ),
        )
        json_data = doc.model_dump(by_alias=True)
        assert json_data["_id"] == "json-test-123"
        assert json_data["metadata_content"]["title"] == "Test Paper"
        assert "metadata_object" in json_data
        assert "content" in json_data

    def test_regulatory_to_json_with_sections(self):
        """Test regulatory document with sections exports correctly."""
        doc = RegulatoryDocument(
            _id="reg-json-123",
            metadata_content=RegulatoryMetadataContent(
                document_type=DocumentType.REGULATORY_DOC,
                content_type=ContentType.SUMMARY_510K,
                title="510(k) Summary",
                k_number="K240001",
            ),
        )
        json_data = doc.model_dump(by_alias=True)
        assert "content" in json_data
        assert "sections" in json_data["content"]
