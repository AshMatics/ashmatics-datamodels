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
Tests for governance document models.

Reference: ASHKBAPP-47 - Refactor CAI Framework to Common Datamodels
"""


from ashmatics_datamodels.documents import (
    ContentFormat,
    ControlsDocument,
    DomainType,
    EmbeddingsMeta,
    FrameworkDocument,
    GovernanceArtifactType,
    GovernanceCategory,
    GovernanceCitation,
    GovernanceContent,
    GovernanceMetadataContent,
    GovernancePlaceholder,
    GovernanceSection,
    GovernanceSubcategory,
    GovernanceSummary,
    PolicyBinding,
    PolicyDocument,
    ProcessDocument,
    ProcessDomainCode,
    SOPDocument,
    TraceabilityInfo,
    WorkProductDocument,
)


class TestGovernanceEnums:
    """Test governance enumeration values."""

    def test_process_domain_codes(self):
        """Test all process domain codes are defined."""
        assert ProcessDomainCode.PV == "PV"
        assert ProcessDomainCode.SA == "SA"
        assert ProcessDomainCode.MON == "MON"
        assert ProcessDomainCode.OVR == "OVR"
        assert ProcessDomainCode.ORG == "ORG"
        assert ProcessDomainCode.IT == "IT"
        assert ProcessDomainCode.RM == "RM"
        assert ProcessDomainCode.HO == "HO"
        assert ProcessDomainCode.EF == "EF"
        assert ProcessDomainCode.TR == "TR"
        assert ProcessDomainCode.UG == "UG"
        assert ProcessDomainCode.XX == "XX"
        assert ProcessDomainCode.YY == "YY"

    def test_governance_categories(self):
        """Test governance category values."""
        assert GovernanceCategory.CAI_GOVERNANCE == "cai_governance"
        assert GovernanceCategory.POLICY_DOMAIN == "policy_domain"
        assert GovernanceCategory.PROCESS_DOMAIN == "process_domain"

    def test_domain_types(self):
        """Test domain type values."""
        assert DomainType.PROCESS == "process"
        assert DomainType.POLICY == "policy"
        assert DomainType.CONTROLS == "controls"
        assert DomainType.GOVERNANCE == "governance"


class TestGovernanceContentComponents:
    """Test governance content component models."""

    def test_governance_placeholder(self):
        """Test placeholder model creation."""
        placeholder = GovernancePlaceholder(
            token="{{ORGANIZATION_NAME}}",
            name="ORGANIZATION_NAME",
            required=True,
            context="The {{ORGANIZATION_NAME}} shall ensure...",
        )
        assert placeholder.token == "{{ORGANIZATION_NAME}}"
        assert placeholder.name == "ORGANIZATION_NAME"
        assert placeholder.required is True

    def test_policy_binding(self):
        """Test policy binding model creation."""
        binding = PolicyBinding(
            binding_type="policy",
            code="PV-01",
            reference="Policy PV-01: Problem Identification",
            context="According to Policy PV-01...",
        )
        assert binding.binding_type == "policy"
        assert binding.code == "PV-01"

    def test_traceability_info(self):
        """Test traceability info model creation."""
        trace = TraceabilityInfo(
            process_outputs=["PO-001", "PO-002"],
            contributes_to=["PO-003"],
            depends_on=["PO-000"],
        )
        assert len(trace.process_outputs) == 2
        assert "PO-001" in trace.process_outputs

    def test_governance_citation(self):
        """Test governance citation model creation."""
        citation = GovernanceCitation(
            text="ISO 42001:2023",
            url="https://www.iso.org/standard/81230.html",
            citation_type="standard",
        )
        assert citation.text == "ISO 42001:2023"
        assert citation.citation_type == "standard"

    def test_embeddings_meta(self):
        """Test embeddings metadata model creation."""
        meta = EmbeddingsMeta(
            needs_embedding=True,
            embedding_model="text-embedding-ada-002",
        )
        assert meta.needs_embedding is True
        assert meta.embedding_model == "text-embedding-ada-002"


class TestGovernanceSection:
    """Test governance section model."""

    def test_basic_section(self):
        """Test basic section creation."""
        section = GovernanceSection(
            level=1,
            title="Introduction",
            anchor="introduction",
            content="This document describes...",
        )
        assert section.level == 1
        assert section.title == "Introduction"
        assert section.anchor == "introduction"

    def test_nested_sections(self):
        """Test nested section structure."""
        subsection = GovernanceSection(
            level=2,
            title="Overview",
            anchor="overview",
            content="The overview section...",
        )
        section = GovernanceSection(
            level=1,
            title="Introduction",
            anchor="introduction",
            content="This document describes...",
            subsections=[subsection],
        )
        assert len(section.subsections) == 1
        assert section.subsections[0].title == "Overview"


class TestGovernanceMetadataContent:
    """Test governance metadata content model."""

    def test_metadata_creation(self):
        """Test metadata content creation with required fields."""
        metadata = GovernanceMetadataContent(
            title="SOP-OVR-03: Performance Monitoring",
            artifact_id="process_domain_sop_ovr_03_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_SOP,
            relative_path="ash-gov-process-model/OVR/SOP-OVR-03.md",
        )
        assert metadata.title == "SOP-OVR-03: Performance Monitoring"
        assert metadata.content_category == GovernanceCategory.PROCESS_DOMAIN

    def test_metadata_with_all_fields(self):
        """Test metadata content with all optional fields."""
        metadata = GovernanceMetadataContent(
            title="SOP-OVR-03: Performance Monitoring",
            artifact_id="process_domain_sop_ovr_03_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_SOP,
            subcategory_label="sop",
            process_domain_code=ProcessDomainCode.OVR,
            content_format=ContentFormat.MARKDOWN,
            domain_type=DomainType.PROCESS,
            domain_code="OVR",
            domain_name="Oversight & Steering",
            relative_path="ash-gov-process-model/OVR/SOP-OVR-03.md",
            framework_version="0.7.0",
            content_hash="abc123def456",
        )
        assert metadata.process_domain_code == ProcessDomainCode.OVR
        assert metadata.domain_type == DomainType.PROCESS


class TestGovernanceContent:
    """Test governance content model."""

    def test_content_creation(self):
        """Test content creation with defaults."""
        content = GovernanceContent()
        assert content.governance_sections == []
        assert content.placeholders == []
        assert content.policy_bindings == []
        assert content.tokens_required == 0

    def test_content_with_data(self):
        """Test content with populated fields."""
        content = GovernanceContent(
            governance_sections=[
                GovernanceSection(level=1, title="Introduction", anchor="intro"),
            ],
            placeholders=[
                GovernancePlaceholder(token="{{NAME}}", name="NAME", required=True),
            ],
            policy_bindings=[
                PolicyBinding(
                    binding_type="policy", code="PV-01", reference="Policy PV-01"
                ),
            ],
            normative_refs=["ISO 42001", "NIST AI RMF"],
            tokens_required=1500,
        )
        assert len(content.governance_sections) == 1
        assert len(content.placeholders) == 1
        assert len(content.policy_bindings) == 1
        assert len(content.normative_refs) == 2
        assert content.tokens_required == 1500


class TestPolicyDocument:
    """Test PolicyDocument model."""

    def test_policy_document_creation(self):
        """Test policy document creation."""
        metadata = GovernanceMetadataContent(
            title="Human Oversight Domain Overview",
            artifact_id="policy_domain_ho_overview_abc123",
            content_category=GovernanceCategory.POLICY_DOMAIN,
            subcategory=GovernanceSubcategory.POLICY_DOMAIN_OVERVIEW_CONTENT,
            relative_path="policy-domain/humanOversight-Domain-Overview-Summary.md",
        )
        doc = PolicyDocument(
            metadata_content=metadata,
            policy_type="overview",
            applicable_domains=["HO", "OVR"],
        )
        assert doc.artifact_type == GovernanceArtifactType.POLICY
        assert doc.policy_type == "overview"
        assert "HO" in doc.applicable_domains


class TestSOPDocument:
    """Test SOPDocument model."""

    def test_sop_document_creation(self):
        """Test SOP document creation."""
        metadata = GovernanceMetadataContent(
            title="SOP-OVR-03: Performance Monitoring",
            artifact_id="process_domain_sop_ovr_03_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_SOP,
            relative_path="ash-gov-process-model/OVR/SOP-OVR-03.md",
        )
        doc = SOPDocument(
            metadata_content=metadata,
            sop_code="SOP-OVR-03",
            process_area="Oversight & Steering",
        )
        assert doc.artifact_type == GovernanceArtifactType.SOP
        assert doc.sop_code == "SOP-OVR-03"
        assert doc.process_area == "Oversight & Steering"


class TestWorkProductDocument:
    """Test WorkProductDocument model."""

    def test_work_product_creation(self):
        """Test work product document creation."""
        metadata = GovernanceMetadataContent(
            title="WP-RM-02: Risk Assessment Template",
            artifact_id="process_domain_wp_rm_02_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_WORK_PRODUCTS,
            relative_path="ash-gov-process-model/RM/WP-RM-02.md",
        )
        doc = WorkProductDocument(
            metadata_content=metadata,
            wp_code="WP-RM-02",
            output_type="template",
            is_wizard=False,
            contributes_to_outputs=["PO-RM-001"],
        )
        assert doc.artifact_type == GovernanceArtifactType.WORK_PRODUCT
        assert doc.wp_code == "WP-RM-02"
        assert doc.is_wizard is False

    def test_wizard_guide(self):
        """Test wizard guide work product."""
        metadata = GovernanceMetadataContent(
            title="WP-RM-02 Wizard Guide",
            artifact_id="process_domain_wp_rm_02_wizard_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_WIZARD_GUIDES,
            relative_path="ash-gov-process-model/RM/WP-RM-02-Wizard-Guide.md",
        )
        doc = WorkProductDocument(
            metadata_content=metadata,
            wp_code="WP-RM-02",
            output_type="guide",
            is_wizard=True,
        )
        assert doc.is_wizard is True


class TestProcessDocument:
    """Test ProcessDocument model."""

    def test_process_document_creation(self):
        """Test process document creation."""
        metadata = GovernanceMetadataContent(
            title="Area 5: Oversight & Steering",
            artifact_id="process_domain_area_5_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_BASE_DOCUMENTS,
            relative_path="ash-gov-process-model/AshmaticsAIGov-Area5-OVR.md",
        )
        doc = ProcessDocument(
            metadata_content=metadata,
            process_area_code="OVR",
            process_area_name="Oversight & Steering",
            process_area_number=5,
            related_sops=["SOP-OVR-01", "SOP-OVR-02", "SOP-OVR-03"],
            related_wps=["WP-OVR-01"],
        )
        assert doc.artifact_type == GovernanceArtifactType.PROCESS
        assert doc.process_area_code == "OVR"
        assert doc.process_area_number == 5
        assert len(doc.related_sops) == 3


class TestFrameworkDocument:
    """Test FrameworkDocument model."""

    def test_framework_overview(self):
        """Test framework overview document creation."""
        metadata = GovernanceMetadataContent(
            title="Framework Overview Summary",
            artifact_id="framework_overview_abc123",
            content_category=GovernanceCategory.CAI_GOVERNANCE,
            subcategory=GovernanceSubcategory.CAI_GOVERNANCE_OVERVIEW,
            relative_path="Framework-Overview-Summary.md",
        )
        doc = FrameworkDocument(
            metadata_content=metadata,
            framework_component="overview",
        )
        assert doc.artifact_type == GovernanceArtifactType.FRAMEWORK
        assert doc.framework_component == "overview"


class TestControlsDocument:
    """Test ControlsDocument model."""

    def test_controls_document_creation(self):
        """Test controls document creation."""
        metadata = GovernanceMetadataContent(
            title="ISO 42001 Mapping",
            artifact_id="controls_iso_mapping_abc123",
            content_category=GovernanceCategory.VALIDATION_TOOLS,
            subcategory=GovernanceSubcategory.CONTROLS_ISO_MAPPINGS,
            relative_path="ISO-42001-maps/iso-mapping.json",
        )
        doc = ControlsDocument(
            metadata_content=metadata,
            control_framework="ISO-42001",
            mapping_type="iso_mapping",
        )
        assert doc.artifact_type == GovernanceArtifactType.CONTROLS
        assert doc.control_framework == "ISO-42001"


class TestGovernanceSummary:
    """Test GovernanceSummary model."""

    def test_summary_from_document(self):
        """Test creating summary from full document."""
        metadata = GovernanceMetadataContent(
            title="SOP-OVR-03: Performance Monitoring",
            artifact_id="process_domain_sop_ovr_03_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_SOP,
            process_domain_code=ProcessDomainCode.OVR,
            domain_name="Oversight & Steering",
            relative_path="ash-gov-process-model/OVR/SOP-OVR-03.md",
            framework_version="0.7.0",
        )
        content = GovernanceContent(tokens_required=2500)
        doc = SOPDocument(
            id="mongo_id_123",
            metadata_content=metadata,
            content=content,
            sop_code="SOP-OVR-03",
        )

        summary = GovernanceSummary.from_document(doc)
        assert summary.title == "SOP-OVR-03: Performance Monitoring"
        assert summary.artifact_type == GovernanceArtifactType.SOP
        assert summary.framework_version == "0.7.0"
        assert summary.artifact_id == "process_domain_sop_ovr_03_abc123"
        assert summary.process_domain_code == ProcessDomainCode.OVR
        assert summary.tokens_required == 2500


class TestDocumentSerialization:
    """Test document serialization to dict/JSON."""

    def test_policy_document_to_dict(self):
        """Test policy document serialization."""
        metadata = GovernanceMetadataContent(
            title="Test Policy",
            artifact_id="test_policy_abc123",
            content_category=GovernanceCategory.POLICY_DOMAIN,
            subcategory=GovernanceSubcategory.POLICY_DOMAIN_OVERVIEW_CONTENT,
            relative_path="policy-domain/test.md",
        )
        doc = PolicyDocument(
            metadata_content=metadata,
            policy_type="overview",
        )

        data = doc.model_dump(by_alias=True)
        assert data["metadata_content"]["title"] == "Test Policy"
        assert data["policy_type"] == "overview"
        assert "_framework_schema" in data
        assert data["_framework_schema"] == "v1"

    def test_sop_document_to_dict(self):
        """Test SOP document serialization."""
        metadata = GovernanceMetadataContent(
            title="SOP-TEST-01",
            artifact_id="sop_test_01_abc123",
            content_category=GovernanceCategory.PROCESS_DOMAIN,
            subcategory=GovernanceSubcategory.PROCESS_DOMAIN_SOP,
            relative_path="test/SOP-TEST-01.md",
        )
        doc = SOPDocument(
            metadata_content=metadata,
            sop_code="SOP-TEST-01",
            process_area="Test Area",
        )

        data = doc.model_dump(by_alias=True)
        assert data["sop_code"] == "SOP-TEST-01"
        assert data["process_area"] == "Test Area"
