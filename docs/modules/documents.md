# documents/ Module

The `documents/` module provides MongoDB three-tier document schemas for all `kb_*` collections.

## Three-Tier Architecture

All documents follow a standardized three-tier structure:

```
MongoDocumentBase
├── Tier 1: metadata_object    (Artifact/file metadata)
├── Tier 2: metadata_content   (Content classification)
└── Tier 3: content            (Document body)
```

### Design Benefits

- **Separation of concerns** - Storage vs content vs classification
- **Consistent queries** - All collections have same top-level structure
- **Efficient search** - Filter on metadata without loading full content
- **Flexible content** - Different document types extend base content

## Base Classes

### MongoDocumentBase

Foundation for all document types.

```python
from ashmatics_datamodels.documents import (
    MongoDocumentBase,
    MetadataObjectBase,
    MetadataContentBase,
    ContentBase,
)

doc = MongoDocumentBase(
    _id="doc-001",
    metadata_object=MetadataObjectBase(...),
    metadata_content=MetadataContentBase(...),
    content=ContentBase(...),
)
```

### MetadataObjectBase (Tier 1)

Artifact and file metadata.

```python
from ashmatics_datamodels.documents import MetadataObjectBase

meta_obj = MetadataObjectBase(
    created_at=datetime.now(timezone.utc),
    created_by="system",
    version="1.0",
    storage_location="s3://kb/papers/file.pdf",
    file_size_bytes=1024000,
    checksum_md5="abc123",
    processing_pipeline="grobid_v0.7.2",
)
```

**Fields:**
- Timestamps (created_at, updated_at)
- Provenance (created_by, version)
- Storage (location, size, checksum, filename)
- Processing (pipeline, completion time, errors)

### MetadataContentBase (Tier 2)

Content classification metadata.

```python
from ashmatics_datamodels.documents import (
    MetadataContentBase,
    DocumentType,
    ContentType,
)

meta_content = MetadataContentBase(
    document_type=DocumentType.EVIDENCE_DOC,
    content_type=ContentType.PEER_REVIEWED_PAPER,
    title="Deep Learning for Radiology",
    language="en",
    tags=["ai", "radiology", "deep-learning"],
    clinical_domain="radiology",
    keywords=["neural networks", "image analysis"],
)
```

**Fields:**
- Document classification (document_type, content_type)
- Searchable text (title, abstract, keywords)
- Categorization (clinical_domain, tags)
- Language and metadata

### ContentBase (Tier 3)

Document body with hierarchical sections.

```python
from ashmatics_datamodels.documents import (
    ContentBase,
    SectionBase,
    FigureReference,
    TableReference,
    CitationReference,
)

content = ContentBase(
    sections={
        "1_intro": SectionBase(title="Introduction", order=1, text="..."),
        "2_methods": SectionBase(title="Methods", order=2, text="..."),
    },
    figures=[
        FigureReference(
            figure_id="fig1",
            caption="Model architecture",
            image_url="s3://kb/figures/fig1.png",
        )
    ],
    tables=[
        TableReference(
            table_id="table1",
            caption="Performance metrics",
            data=[{"metric": "accuracy", "value": 0.95}],
        )
    ],
    references=[
        CitationReference(
            ref_id="ref1",
            citation="Smith et al. (2024)",
            doi="10.1234/example",
        )
    ],
)
```

## Document Types

### EvidenceDocument

Scientific evidence and publications (`kb_evidence_doc`).

```python
from ashmatics_datamodels.documents import (
    EvidenceDocument,
    EvidenceMetadataContent,
    DocumentType,
    ContentType,
)

doc = EvidenceDocument(
    _id="evidence-001",
    metadata_content=EvidenceMetadataContent(
        document_type=DocumentType.EVIDENCE_DOC,
        content_type=ContentType.PEER_REVIEWED_PAPER,
        title="AI in Emergency Radiology",
        authors=["Dr. Smith", "Dr. Jones"],
        journal="Radiology",
        doi="10.1148/radiol.2024123456",
        publication_date=date(2024, 3, 15),
        clinical_domain="radiology",
        anatomical_region="chest",
        pathology_focus=["pneumonia"],
    ),
)
```

**Evidence-specific fields:**
- Authors, journal, DOI, PubMed ID
- Publication date
- Anatomical region and pathology focus
- Study design and sample size

### RegulatoryDocument

Regulatory submissions (`kb_regulatory_doc`).

```python
from ashmatics_datamodels.documents import (
    RegulatoryDocument,
    RegulatoryMetadataContent,
    PredicateDeviceInfo,
)

doc = RegulatoryDocument(
    _id="reg-k240001",
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
    ),
)

# Add predicate device
doc.content.predicate_device = PredicateDeviceInfo(
    k_number="K190123",
    device_name="ChestView AI",
    manufacturer="Competitor Inc",
)
```

**Regulatory-specific fields:**
- K number, PMA number, or De Novo number
- Clearance/approval date
- Device class and product code
- Predicate device information

### SystemCardDocument and IfuDocument

AI system cards (`kb_aisystem_card`) and instructions for use (`kb_ifu_doc`), vendor system
documents (0.24.0; they replaced `ModelCardDocument` and `kb_aimodel_card`).

```python
from ashmatics_datamodels.documents import (
    ModelPart,
    MonitoringMetric,
    SystemCardContent,
    SystemCardDocument,
    SystemCardMetadataContent,
    SystemDocumentSection,
)

doc = SystemCardDocument(
    metadata_content=SystemCardMetadataContent(
        title="Chart Review Agent (Clinical Summaries) Model Card",
        system_name="Oracle Health Clinical AI Agent, Chart Review Agent (Clinical Summaries)",
        system_version="26.09",
        release_date="2026-09",
        model_type="Summarization",
        developer="Oracle Health",
        third_party_information="OpenAI Platform",
    ),
    content=SystemCardContent(
        sections={
            "external_validation": SystemDocumentSection(
                title="External Validation",
                order=1,
                text="Not available. No external validation was conducted.",
                stated_absent=True,
            ),
        },
        monitoring=[
            MonitoringMetric(
                category="performance",
                metric="Precision",
                automated_or_manual="Manual",
                frequency="Monthly",
            ),
        ],
        model_parts=[ModelPart(name="GPT-5.4", role="large language model", third_party=True)],
    ),
)
```

A vendor's HTI-1 source-attribute card is a system card even when the vendor titles it a model
card. The models inside are `ModelPart` entries, zero or more; there is no model-card document
kind. Section keys are `SYSTEM_CARD_SECTION_NAMES`; any other key is refused.

`IfuDocument` (`kb_ifu_doc`) is the same shape for instructions for use: `IfuMetadataContent`
requires `catalogue_number` and `product_name`, and section keys are `IFU_SECTION_NAMES`.

### ProductCardDocument

Product profiles (`kb_product_card`).

```python
from ashmatics_datamodels.documents import (
    ProductCardDocument,
    ProductCardMetadataContent,
)

doc = ProductCardDocument(
    _id="product-001",
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
```

### ManufacturerCardDocument

Manufacturer profiles (`kb_manufacturer_card`).

```python
from ashmatics_datamodels.documents import (
    ManufacturerCardDocument,
    ManufacturerCardMetadataContent,
)

doc = ManufacturerCardDocument(
    _id="mfr-001",
    metadata_content=ManufacturerCardMetadataContent(
        document_type=DocumentType.MANUFACTURER_CARD,
        content_type=ContentType.COMPANY_PROFILE,
        title="Medical AI Corp Company Profile",
        company_name="Medical AI Corp",
        headquarters="San Francisco, CA",
        founded="2018",
    ),
)
```

### UseCaseDocument

Clinical use case documents (`kb_use_case`).

```python
from ashmatics_datamodels.documents import (
    UseCaseDocument,
    UseCaseMetadataContent,
)

doc = UseCaseDocument(
    _id="usecase-001",
    metadata_content=UseCaseMetadataContent(
        document_type=DocumentType.USE_CASE,
        content_type=ContentType.CLINICAL_USE_CASE,
        title="ED Pneumonia Triage",
        clinical_domain="radiology",
        clinical_specialty="Emergency Medicine",
        anatomical_region="chest",
        pathology=["pneumonia"],
    ),
)
```

## Document Summaries

Lightweight summaries for list views.

```python
from ashmatics_datamodels.documents import EvidenceSummary

# Full document
full_doc = EvidenceDocument(...)

# Create summary (no content)
summary = EvidenceSummary.from_document(full_doc)

# Summary contains only:
# - id, title, authors, journal
# - clinical_domain, tags
# - created_at, updated_at
```

**Available summaries:**
- `EvidenceSummary`
- `DocumentSummaryBase` (generic)

## Hierarchical Sections

Create nested document structure:

```python
from ashmatics_datamodels.documents import SectionBase

# Top-level section with subsections
methods = SectionBase(
    title="Methods",
    order=2,
    text="Methods overview...",
    subsections={
        "2.1_study_design": SectionBase(
            title="Study Design",
            order=1,
            text="Retrospective cohort study...",
        ),
        "2.2_data_collection": SectionBase(
            title="Data Collection",
            order=2,
            text="Data collected from 5 hospitals...",
            subsections={
                "2.2.1_inclusion": SectionBase(
                    title="Inclusion Criteria",
                    order=1,
                    text="Patients with chest X-rays...",
                ),
            },
        ),
    },
)
```

## File Reference

| File | Purpose |
|------|---------|
| `base.py` | Three-tier base classes and enums |
| `evidence.py` | Evidence/publication documents |
| `regulatory.py` | Regulatory documents (510k) |
| `models.py` | AI model card documents |
| `products.py` | Product profile documents |
| `manufacturers.py` | Manufacturer profile documents |
| `use_cases.py` | Clinical use case documents |

## Complete API Reference

For detailed API documentation, see [API Reference: documents](../api/documents.md).
