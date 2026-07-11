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
Regulatory document schemas for kb_regulatory_docs collection.

FDA 510(k) summaries, PMA summaries, and De Novo summaries
with structured sections for device description, indications,
predicates, and performance testing.

Phase 2E (2025-11-25): Added comprehensive performance data models:
- StudyType, MetricType enums for standardized classification
- PerformanceMetric for individual metrics with statistical context
- TestDataset for validation dataset characteristics
- ValidationStudy for study design and methodology
- Enhanced PerformanceTestResults with structured validation data

Reference: docs/Plans/DocumentDataModelSchema-Normalize-2025-11-15/
Vocabulary: https://open.fda.gov/device/510k/
"""

from datetime import date
from enum import Enum
from typing import Annotated, Any, Optional, Union

from pydantic import Discriminator, Field, Tag

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.documents.base import (
    ContentBase,
    ContentType,
    DocumentSummaryBase,
    DocumentType,
    MetadataContentBase,
    MetadataObjectBase,
    MongoDocumentBase,
    RegulatoryPathway,
    RegulatoryRegion,
    SectionBase,
)


# =============================================================================
# Phase 2E Enumerations (Performance Data Extraction)
# =============================================================================


class StudyType(str, Enum):
    """
    Type of validation study (REQ-3.7).

    Used to classify validation studies in FDA 510(k) and De Novo submissions.
    """

    STANDALONE = "standalone"  # Device-only testing with ground truth
    CLINICAL_VALIDATION = "clinical_validation"  # Clinical evaluation study
    READER_STUDY = "reader_study"  # Multi-reader multi-case (MRMC) study
    PIVOTAL_STUDY = "pivotal_study"  # Definitive regulatory validation study
    PILOT_STUDY = "pilot_study"  # Preliminary feasibility study
    RETROSPECTIVE = "retrospective"  # Retrospective chart review/data analysis
    PROSPECTIVE = "prospective"  # Prospective data collection study
    UNKNOWN = "unknown"  # Cannot determine study type


class MetricType(str, Enum):
    """
    Type of performance metric (REQ-3.1).

    Standardized metric types for querying and analysis across devices.
    """

    SENSITIVITY = "sensitivity"  # True positive rate
    SPECIFICITY = "specificity"  # True negative rate
    AUC = "auc"  # Area under ROC curve
    DICE = "dice"  # DICE coefficient (segmentation overlap)
    ACCURACY = "accuracy"  # Overall accuracy
    PPV = "ppv"  # Positive predictive value
    NPV = "npv"  # Negative predictive value
    F1_SCORE = "f1_score"  # F1 score (harmonic mean of precision/recall)
    PRECISION = "precision"  # Precision (same as PPV)
    RECALL = "recall"  # Recall (same as sensitivity)
    HAUSDORFF_DISTANCE = "hausdorff_distance"  # Hausdorff distance (segmentation)
    TIME_TO_DETECTION = "time_to_detection"  # Time to detect finding
    TIME_TO_NOTIFICATION = "time_to_notification"  # Time to notify clinician
    DETECTION_RATE = "detection_rate"  # Detection rate (e.g., adenoma, fracture)
    FALSE_POSITIVE_RATE = "false_positive_rate"  # False positive rate
    OTHER = "other"  # Other metric types not in standard list


# =============================================================================
# Regulatory-Specific Nested Schemas
# =============================================================================


class RawSection(SectionBase):
    """
    Raw parsed section from document parser (e.g., Docling).

    Stores all sections parsed from the original document,
    not just the enriched/normalized sections. Enables full
    document reconstruction and verification.
    """

    section_id: str = Field(
        ...,
        description="Unique identifier for this raw section (e.g., 'section_1')",
    )
    normalized_to: Optional[str] = Field(
        None,
        description="Key of enriched section this maps to (e.g., '2_indications_for_use'). None if not normalized.",
    )


class StructuredIndication(AshMaticsBaseModel):
    """Structured representation of indications for use."""

    anatomical_region: Optional[str] = Field(
        None,
        description="Target anatomical region",
    )
    modality: Optional[str] = Field(
        None,
        description="Imaging or diagnostic modality",
    )
    clinical_application: Optional[str] = Field(
        None,
        description="Primary clinical application",
    )
    patient_population: Optional[str] = Field(
        None,
        description="Target patient population",
    )


class PredicateDeviceInfo(AshMaticsBaseModel):
    """Information about a predicate device for substantial equivalence."""

    k_number: str = Field(
        ...,
        description="510(k) number of predicate device",
    )
    device_name: Optional[str] = Field(
        None,
        description="Name of the predicate device",
    )
    manufacturer: Optional[str] = Field(
        None,
        description="Manufacturer of predicate device",
    )
    comparison_summary: Optional[str] = Field(
        None,
        description="Summary of comparison to predicate",
    )


# =============================================================================
# Patient and Dataset Models (shared by Phase 2D and 2E)
# =============================================================================


class PatientDemographics(AshMaticsBaseModel):
    """Patient demographics for training/validation datasets (REQ-2.2)."""

    age_range: Optional[str] = Field(
        None,
        description="Age range of patients (e.g., '18-85 years')",
    )
    gender_distribution: Optional[dict[str, float]] = Field(
        None,
        description="Gender distribution (e.g., {'male': 0.52, 'female': 0.48})",
    )
    race_ethnicity_distribution: Optional[dict[str, float]] = Field(
        None,
        description="Race/ethnicity distribution per FDA guidance",
    )
    additional_demographics: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional demographic characteristics",
    )


class DatasetCharacteristics(AshMaticsBaseModel):
    """Dataset characteristics for AI/ML training data (REQ-2)."""

    dataset_size: Optional[int] = Field(
        None,
        ge=0,
        description="Total number of samples/images/patients (REQ-2.1)",
    )
    data_source: Optional[str] = Field(
        None,
        description="Source of data (e.g., institution names, public datasets) (REQ-2.4)",
    )
    multi_site: Optional[bool] = Field(
        None,
        description="Whether data collected from multiple sites (REQ-2.4)",
    )
    imaging_modality: Optional[str] = Field(
        None,
        description="Imaging modality/device type for data acquisition (REQ-2.6)",
    )
    ground_truth_method: Optional[str] = Field(
        None,
        description="Ground truth/reference standard methodology (REQ-2.7)",
    )
    additional_characteristics: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional dataset characteristics",
    )


# =============================================================================
# Phase 2E Performance Data Models (REQ-3)
# =============================================================================


class PerformanceMetric(AshMaticsBaseModel):
    """
    Individual performance metric with statistical context and stratification.

    Addresses REQ-3.1 (Performance Metrics Extraction) from Phase 2E design plan.
    Captures quantitative performance metrics with confidence intervals, p-values,
    and stratification dimensions for comparative effectiveness analysis.

    Example:
        >>> metric = PerformanceMetric(
        ...     metric_name="sensitivity",
        ...     metric_type=MetricType.SENSITIVITY,
        ...     value=0.906,
        ...     ci_lower=0.822,
        ...     ci_upper=0.959,
        ...     sample_size=184,
        ...     stratification={"study": "pivotal", "site": "multi_site"},
        ...     source_table="table_18"
        ... )
    """

    metric_name: str = Field(
        ...,
        description="Metric name as appears in document (e.g., 'sensitivity', 'DICE', 'AUC')",
    )
    metric_type: Optional[MetricType] = Field(
        None,
        description="Standardized metric type for querying across devices",
    )
    value: float = Field(
        ...,
        description="Metric value (proportion 0-1 for percentages, raw value otherwise)",
    )
    unit: Optional[str] = Field(
        None,
        description="Unit if applicable (e.g., 'seconds', 'mm', 'minutes')",
    )

    # Statistical measures (REQ-3.3)
    ci_lower: Optional[float] = Field(
        None,
        description="95% confidence interval lower bound",
    )
    ci_upper: Optional[float] = Field(
        None,
        description="95% confidence interval upper bound",
    )
    p_value: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="p-value for statistical testing",
    )
    standard_error: Optional[float] = Field(
        None,
        ge=0.0,
        description="Standard error of metric",
    )
    sample_size: Optional[int] = Field(
        None,
        ge=0,
        description="Sample size (N) for this metric calculation",
    )

    # Stratification (REQ-3.4)
    stratification: Optional[dict[str, str]] = Field(
        None,
        description="Stratification dimensions (e.g., {'gender': 'female', 'age_group': '50-70', 'study': 'pivotal'})",
    )

    # Source attribution (REQ-8.1)
    source_table: Optional[str] = Field(
        None,
        description="Source table ID (e.g., 'table_18')",
    )
    source_section: Optional[str] = Field(
        None,
        description="Source section if extracted from narrative text",
    )


class TestDataset(AshMaticsBaseModel):
    """
    Characteristics of a validation/test dataset.

    Addresses REQ-3.2 (Validation Dataset Characteristics) from Phase 2E design plan.
    Captures dataset size, demographics, clinical characteristics, and relationship
    to training data for proper contextualization of performance results.

    Example:
        >>> dataset = TestDataset(
        ...     dataset_name="Pivotal Study Cohort",
        ...     dataset_size=184,
        ...     data_source="3 clinical sites (2 US, 1 OUS)",
        ...     multi_site=True,
        ...     num_sites=3,
        ...     ground_truth_method="Consensus of 3 board-certified radiologists"
        ... )
    """

    dataset_name: Optional[str] = Field(
        None,
        description="Dataset name/description (e.g., 'Pivotal Study Cohort', 'External Validation Set')",
    )
    dataset_size: Optional[int] = Field(
        None,
        ge=0,
        description="Total number of cases/images/patients",
    )
    data_source: Optional[str] = Field(
        None,
        description="Source institutions or description",
    )
    multi_site: Optional[bool] = Field(
        None,
        description="Whether data collected from multiple sites",
    )
    num_sites: Optional[int] = Field(
        None,
        ge=0,
        description="Number of sites if multi-site",
    )
    collection_period: Optional[str] = Field(
        None,
        description="Time period for data collection (e.g., 'Jan 2020 - Dec 2022')",
    )
    ground_truth_method: Optional[str] = Field(
        None,
        description="Ground truth/reference standard methodology",
    )
    imaging_modality: Optional[str] = Field(
        None,
        description="Imaging modality/acquisition parameters",
    )

    # Patient demographics (REQ-3.2)
    patient_demographics: Optional[PatientDemographics] = Field(
        None,
        description="Patient demographics for validation dataset",
    )

    # Clinical characteristics
    disease_prevalence: Optional[str] = Field(
        None,
        description="Disease prevalence in dataset (e.g., '45% positive cases')",
    )
    inclusion_criteria: Optional[str] = Field(
        None,
        description="Inclusion criteria for dataset",
    )
    exclusion_criteria: Optional[str] = Field(
        None,
        description="Exclusion criteria for dataset",
    )

    # Relationship to training data
    independent_from_training: Optional[bool] = Field(
        None,
        description="Whether dataset is independent from training data (temporal, site, or patient separation)",
    )


class ValidationStudy(AshMaticsBaseModel):
    """
    Validation study design and characteristics.

    Addresses REQ-3.7 (Test Methodology and Study Design) from Phase 2E design plan.
    Captures study type, design elements (blinding, control), and links to
    test dataset and acceptance criteria.

    Example:
        >>> study = ValidationStudy(
        ...     study_name="Pivotal Study",
        ...     study_type=StudyType.PIVOTAL_STUDY,
        ...     prospective=False,
        ...     blinding="single_blind",
        ...     num_readers=5,
        ...     num_cases=184,
        ...     test_dataset=TestDataset(dataset_size=184, multi_site=True),
        ...     acceptance_criteria="Sensitivity and specificity >= 80%",
        ...     acceptance_met=True
        ... )
    """

    study_name: Optional[str] = Field(
        None,
        description="Study name (e.g., 'Pivotal Study', 'Pilot Study', 'Reader Study')",
    )
    study_type: StudyType = Field(
        ...,
        description="Type of validation study",
    )
    study_description: Optional[str] = Field(
        None,
        description="Brief study description",
    )

    # Study design (REQ-3.7)
    prospective: Optional[bool] = Field(
        None,
        description="Prospective (True) vs retrospective (False) study design",
    )
    blinding: Optional[str] = Field(
        None,
        description="Blinding approach (e.g., 'single_blind', 'double_blind', 'unblinded')",
    )
    control_type: Optional[str] = Field(
        None,
        description="Control/comparison type (e.g., 'ground_truth', 'predicate', 'reader_alone')",
    )

    # MRMC-specific fields
    num_readers: Optional[int] = Field(
        None,
        ge=0,
        description="Number of readers for MRMC study",
    )
    num_cases: Optional[int] = Field(
        None,
        ge=0,
        description="Number of cases evaluated",
    )

    # Test dataset
    test_dataset: Optional[TestDataset] = Field(
        None,
        description="Validation dataset characteristics",
    )

    # Acceptance criteria (REQ-3.6)
    acceptance_criteria: Optional[str] = Field(
        None,
        description="Acceptance criteria for study (e.g., 'Sensitivity >= 85%')",
    )
    acceptance_met: Optional[bool] = Field(
        None,
        description="Whether acceptance criteria were met",
    )

    # Source attribution
    source_section: Optional[str] = Field(
        None,
        description="Source section in document",
    )


class PerformanceTestResults(AshMaticsBaseModel):
    """
    Comprehensive performance testing results container.

    Enhanced in Phase 2E (2025-11-25) with structured validation studies,
    detailed performance metrics with stratification, and predicate comparison.
    Maintains backward compatibility with Phase 1 legacy fields.

    Addresses REQ-3 (Validation Results Extraction) from Phase 2E design plan.

    Example:
        >>> results = PerformanceTestResults(
        ...     validation_studies=[
        ...         ValidationStudy(study_name="Pilot Study", study_type=StudyType.PILOT_STUDY),
        ...         ValidationStudy(study_name="Pivotal Study", study_type=StudyType.PIVOTAL_STUDY)
        ...     ],
        ...     performance_metrics=[
        ...         PerformanceMetric(metric_name="sensitivity", value=0.906, ci_lower=0.822, ci_upper=0.959)
        ...     ],
        ...     extraction_confidence=85.0
        ... )
    """

    # Phase 2E: Validation studies (REQ-3.7)
    validation_studies: list[ValidationStudy] = Field(
        default_factory=list,
        description="List of validation studies (pilot, pivotal, reader study, etc.)",
    )

    # Phase 2E: Performance metrics (REQ-3.1, REQ-3.4)
    performance_metrics: list[PerformanceMetric] = Field(
        default_factory=list,
        description="All extracted performance metrics with stratification",
    )

    # Phase 2E: Predicate comparison (REQ-3.5)
    comparison_to_predicate: Optional[str] = Field(
        None,
        description="Performance comparison to predicate device (e.g., 'Non-inferior', 'Superior')",
    )
    predicate_metrics: list[PerformanceMetric] = Field(
        default_factory=list,
        description="Predicate device performance metrics for comparison",
    )

    # Legacy fields (Phase 1 compatibility) - populated for backward compatibility
    sensitivity: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall sensitivity (legacy field - use performance_metrics for detailed data)",
    )
    specificity: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall specificity (legacy field - use performance_metrics for detailed data)",
    )
    auc_roc: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall AUC (legacy field - use performance_metrics for detailed data)",
    )
    test_dataset_size: Optional[int] = Field(
        None,
        ge=0,
        description="Overall test dataset size (legacy field - use validation_studies for detailed data)",
    )
    additional_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional unstructured metrics (legacy field)",
    )

    # Phase 2E: Extraction metadata
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Confidence score for extracted performance data (0-100)",
    )
    source_tables: list[str] = Field(
        default_factory=list,
        description="List of table IDs from which performance data was extracted",
    )


# =============================================================================
# Phase 2D Training Data Models (REQ-2)
# =============================================================================


class TrainingDataCharacteristics(AshMaticsBaseModel):
    """
    AI/ML training data characteristics for devices using data-driven models.

    Addresses REQ-2 (AI/ML Model Training Data Extraction) from design plan.
    Critical for assessing model generalizability, bias, and applicability
    to specific patient populations.
    """

    dataset_characteristics: Optional[DatasetCharacteristics] = Field(
        None,
        description="Training dataset characteristics (REQ-2.1, 2.4, 2.6, 2.7)",
    )
    patient_demographics: Optional[PatientDemographics] = Field(
        None,
        description="Patient demographics in training data (REQ-2.2)",
    )
    inclusion_criteria: Optional[str] = Field(
        None,
        description="Inclusion criteria for training data (REQ-2.5)",
    )
    exclusion_criteria: Optional[str] = Field(
        None,
        description="Exclusion criteria for training data (REQ-2.5)",
    )
    disease_characteristics: Optional[str] = Field(
        None,
        description="Disease/condition characteristics (severity, stage, comorbidities) (REQ-2.3)",
    )
    data_collection_period: Optional[str] = Field(
        None,
        description="Time period for data collection",
    )
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Confidence score for extracted training data information (0-100)",
    )
    source_tables: list[str] = Field(
        default_factory=list,
        description="List of table IDs from which training data was extracted",
    )


# =============================================================================
# Regulatory-Specific Sections
# =============================================================================


class SponsorSection(SectionBase):
    """
    Sponsor/Applicant identification section.

    Contains sponsor company information, contact details,
    and submission metadata commonly found at the beginning
    of 510(k) and De Novo summary documents.
    """

    title: str = Field(default="Sponsor Information", description="Section title")
    order: int = Field(default=0, description="Section order")


class DeviceDescriptionSection(SectionBase):
    """Device description section with structured fields."""

    title: str = Field(default="Device Description", description="Section title")
    order: int = Field(default=1, description="Section order")


class IndicationsSection(SectionBase):
    """Indications for use section with structured data."""

    title: str = Field(default="Indications for Use", description="Section title")
    order: int = Field(default=2, description="Section order")
    structured_indications: Optional[StructuredIndication] = Field(
        None,
        description="Structured indication data",
    )


class PredicatesSection(SectionBase):
    """Predicate devices section."""

    title: str = Field(default="Predicate Devices", description="Section title")
    order: int = Field(default=3, description="Section order")
    predicates: list[PredicateDeviceInfo] = Field(
        default_factory=list,
        description="List of predicate devices",
    )


class PerformanceTestingSection(SectionBase):
    """
    Performance testing section with comprehensive results and training data.

    Enhanced in Phase 2E (2025-11-25) with structured validation studies,
    detailed performance metrics with statistical context and stratification.

    Contains:
    - test_results: Comprehensive performance test results (Phase 2E, REQ-3)
      - validation_studies: Pilot, pivotal, reader studies with design details
      - performance_metrics: All metrics with CIs, p-values, stratification
      - predicate_metrics: Predicate device performance for comparison
    - training_data: AI/ML training data characteristics (Phase 2D, REQ-2)
    """

    title: str = Field(default="Performance Testing", description="Section title")
    order: int = Field(default=4, description="Section order")
    test_results: Optional[PerformanceTestResults] = Field(
        None,
        description="Comprehensive structured performance test results (Phase 2E, REQ-3)",
    )
    training_data: Optional[TrainingDataCharacteristics] = Field(
        None,
        description="AI/ML training data characteristics (Phase 2D, REQ-2)",
    )


class SubstantialEquivalenceSection(SectionBase):
    """Substantial equivalence determination section."""

    title: str = Field(default="Substantial Equivalence", description="Section title")
    order: int = Field(default=5, description="Section order")


# =============================================================================
# Regulatory-Specific Metadata Content
# =============================================================================


class RegulatoryMetadataContent(MetadataContentBase):
    """
    Metadata content specific to regulatory documents.

    Extends base metadata with FDA-specific fields aligned
    with OpenFDA vocabulary.
    """

    document_type: DocumentType = Field(
        default=DocumentType.REGULATORY_DOC,
        description="Always 'kb_regulatory_doc' for regulatory documents",
    )
    content_type: ContentType = Field(
        default=ContentType.SUMMARY_510K,
        description="Type of regulatory document",
    )

    # FDA identifiers (OpenFDA aligned)
    k_number: Optional[str] = Field(
        None,
        max_length=10,
        description="510(k) number (e.g., 'K240001')",
    )
    pma_number: Optional[str] = Field(
        None,
        max_length=10,
        description="PMA number (e.g., 'P190001')",
    )
    de_novo_number: Optional[str] = Field(
        None,
        max_length=15,
        description="De Novo number",
    )

    # Device and applicant info
    clearance_date: Optional[date] = Field(
        None,
        description="Date of FDA clearance/approval",
    )
    applicant: Optional[str] = Field(
        None,
        description="Applicant/submitter name",
    )
    device_name: Optional[str] = Field(
        None,
        description="Device name as cleared",
    )
    device_class: Optional[str] = Field(
        None,
        max_length=3,
        description="FDA device class (I, II, III)",
    )
    product_code: Optional[str] = Field(
        None,
        description="FDA three-letter product code(s). Single code (e.g., 'QIH') or comma-separated for multiple (e.g., 'QIH,LLZ')",
    )

    # Regulator scoping (ASHKBAPP-91 split model; ontology-single-sourced)
    regulatory_region: Optional[RegulatoryRegion] = Field(
        None,
        description="Regulatory jurisdiction (US->FDA, UK->MHRA, ...). The regulator axis of the split document_type model.",
        json_schema_extra={"x_ontology_scheme": "ash:RegulatoryRegionScheme"},
    )
    regulatory_pathway: Optional[RegulatoryPathway] = Field(
        None,
        description="Regulatory submission/clearance pathway (510(k), PMA, De Novo, CE, ...).",
        json_schema_extra={"x_ontology_scheme": "ash:RegulatoryPathwayScheme"},
    )

    # Predicate devices (for easy querying)
    predicate_devices: list[str] = Field(
        default_factory=list,
        description="List of predicate device K-numbers (e.g., ['K213882', 'K191928']). Top-level array for easy MongoDB queries.",
    )

    # Advisory committee
    advisory_committee: Optional[str] = Field(
        None,
        max_length=2,
        description="Two-letter advisory committee code",
    )


# =============================================================================
# Section Type Discriminator for Serialization
# =============================================================================


def _get_section_type(v: Any) -> str:
    """
    Discriminator function for RegulatorySection union.

    Used by Pydantic to determine which section subclass to use during
    serialization, ensuring subclass-specific fields (like test_results,
    training_data, predicates) are preserved in the output.
    """
    if isinstance(v, dict):
        # During deserialization, use title to discriminate
        title = v.get("title", "")
        if "Sponsor" in title:
            return "sponsor"
        elif "Device Description" in title:
            return "device_description"
        elif "Indications" in title:
            return "indications"
        elif "Predicate" in title:
            return "predicates"
        elif "Performance" in title or "Testing" in title:
            return "performance_testing"
        elif "Substantial Equivalence" in title:
            return "substantial_equivalence"
        else:
            return "raw"
    # During serialization, use class type
    if isinstance(v, SponsorSection):
        return "sponsor"
    elif isinstance(v, DeviceDescriptionSection):
        return "device_description"
    elif isinstance(v, IndicationsSection):
        return "indications"
    elif isinstance(v, PredicatesSection):
        return "predicates"
    elif isinstance(v, PerformanceTestingSection):
        return "performance_testing"
    elif isinstance(v, SubstantialEquivalenceSection):
        return "substantial_equivalence"
    elif isinstance(v, RawSection):
        return "raw"
    return "raw"  # Default fallback


# Union type for all regulatory section types
# This ensures Pydantic serializes subclass-specific fields correctly
RegulatorySection = Annotated[
    Union[
        Annotated[SponsorSection, Tag("sponsor")],
        Annotated[DeviceDescriptionSection, Tag("device_description")],
        Annotated[IndicationsSection, Tag("indications")],
        Annotated[PredicatesSection, Tag("predicates")],
        Annotated[PerformanceTestingSection, Tag("performance_testing")],
        Annotated[SubstantialEquivalenceSection, Tag("substantial_equivalence")],
        Annotated[RawSection, Tag("raw")],
    ],
    Discriminator(_get_section_type),
]


# =============================================================================
# Regulatory-Specific Content
# =============================================================================


class RegulatoryContent(ContentBase):
    """
    Content structure for regulatory documents.

    Standard 510(k) summary structure with device description,
    indications, predicates, testing, and substantial equivalence.

    Includes both enriched/normalized sections and raw parsed sections
    for complete document preservation and traceability.
    """

    sections: dict[str, RegulatorySection] = Field(  # type: ignore[assignment]
        default_factory=lambda: {
            "0_sponsor": SponsorSection(
                title="Sponsor Information", order=0
            ),
            "1_device_description": DeviceDescriptionSection(
                title="Device Description", order=1
            ),
            "2_indications_for_use": IndicationsSection(
                title="Indications for Use", order=2
            ),
            "3_predicate_devices": PredicatesSection(
                title="Predicate Devices", order=3
            ),
            "4_performance_testing": PerformanceTestingSection(
                title="Performance Testing", order=4
            ),
            "5_substantial_equivalence": SubstantialEquivalenceSection(
                title="Substantial Equivalence", order=5
            ),
        },
        description="Enriched/normalized 510(k) summary sections (Ashmatics value-add)",
    )

    raw_sections: list[RawSection] = Field(
        default_factory=list,
        description="All sections parsed from document (complete content from parser like Docling)",
    )


# =============================================================================
# Complete Regulatory Document
# =============================================================================


class RegulatoryDocument(MongoDocumentBase):
    """
    Complete regulatory document with three-tier structure.

    Used for kb_regulatory_docs MongoDB collection.
    """

    metadata_object: MetadataObjectBase = Field(
        default_factory=MetadataObjectBase,
        description="Artifact metadata",
    )
    metadata_content: RegulatoryMetadataContent = Field(
        ...,
        description="Regulatory-specific metadata",
    )
    content: RegulatoryContent = Field(
        default_factory=RegulatoryContent,
        description="510(k) summary content",
    )


class RegulatoryDocumentCreate(MongoDocumentBase):
    """Schema for creating a new regulatory document."""

    metadata_content: RegulatoryMetadataContent = Field(
        ...,
        description="Required regulatory metadata",
    )
    content: RegulatoryContent = Field(
        default_factory=RegulatoryContent,
        description="Document content",
    )


# =============================================================================
# Regulatory Summary
# =============================================================================


class RegulatorySummary(DocumentSummaryBase):
    """
    Summary view for regulatory documents in listings.

    Flattens key FDA metadata for search results.
    """

    document_type: DocumentType = Field(
        default=DocumentType.REGULATORY_DOC,
        description="Always kb_regulatory_doc",
    )

    # FDA-specific summary fields
    k_number: Optional[str] = Field(
        None,
        description="510(k) number",
    )
    pma_number: Optional[str] = Field(
        None,
        description="PMA number",
    )
    clearance_date: Optional[date] = Field(
        None,
        description="Clearance/approval date",
    )
    applicant: Optional[str] = Field(
        None,
        description="Applicant name",
    )
    device_name: Optional[str] = Field(
        None,
        description="Device name",
    )
    device_class: Optional[str] = Field(
        None,
        description="Device class",
    )
    product_code: Optional[str] = Field(
        None,
        description="Product code",
    )

    @classmethod
    def from_document(cls, doc: RegulatoryDocument) -> "RegulatorySummary":
        """Create summary from full regulatory document."""
        return cls(
            _id=doc.id or "",
            document_type=doc.metadata_content.document_type,
            content_type=doc.metadata_content.content_type,
            title=doc.metadata_content.title,
            clinical_domain=doc.metadata_content.clinical_domain,
            tags=doc.metadata_content.tags,
            created_at=doc.metadata_object.created_at,
            updated_at=doc.metadata_object.updated_at,
            k_number=doc.metadata_content.k_number,
            pma_number=doc.metadata_content.pma_number,
            clearance_date=doc.metadata_content.clearance_date,
            applicant=doc.metadata_content.applicant,
            device_name=doc.metadata_content.device_name,
            device_class=doc.metadata_content.device_class,
            product_code=doc.metadata_content.product_code,
        )
