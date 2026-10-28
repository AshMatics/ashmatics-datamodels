# MongoDB Documents Examples

Examples for working with the three-tier MongoDB document structure.

## Creating an Evidence Document

```python
from ashmatics_datamodels.documents import (
    EvidenceDocument,
    EvidenceMetadataContent,
    MetadataObjectBase,
    ContentBase,
    SectionBase,
    DocumentType,
    ContentType,
)
from datetime import date, datetime, timezone

# Create complete evidence document
doc = EvidenceDocument(
    _id="evidence-2024-001",

    # Tier 1: Artifact metadata
    metadata_object=MetadataObjectBase(
        created_at=datetime.now(timezone.utc),
        created_by="ingestion-pipeline",
        version="1.0",
        storage_location="s3://kb-evidence/papers/smith2024.pdf",
        file_size_bytes=2048000,
        checksum_md5="a1b2c3d4e5f6",
        original_filename="smith_et_al_2024_pneumonia.pdf",
        processing_pipeline="grobid_v0.7.2",
        processing_completed_at=datetime.now(timezone.utc),
    ),

    # Tier 2: Content classification
    metadata_content=EvidenceMetadataContent(
        document_type=DocumentType.EVIDENCE_DOC,
        content_type=ContentType.PEER_REVIEWED_PAPER,
        title="Deep Learning for Pneumonia Detection in Chest X-rays",
        authors=["Dr. Jane Smith", "Dr. John Doe", "Dr. Alice Johnson"],
        journal="Radiology: Artificial Intelligence",
        doi="10.1148/ryai.2024123456",
        pubmed_id="38123456",
        publication_date=date(2024, 3, 15),
        clinical_domain="radiology",
        anatomical_region="chest",
        pathology_focus=["pneumonia", "pleural_effusion"],
        abstract="This study evaluates a deep learning model for pneumonia detection...",
        keywords=["deep learning", "pneumonia", "chest x-ray", "AI"],
        tags=["radiology", "ai", "pneumonia"],
    ),

    # Tier 3: Document body
    content=ContentBase(
        sections={
            "1_introduction": SectionBase(
                title="Introduction",
                order=1,
                text="Pneumonia is a leading cause of morbidity and mortality...",
            ),
            "2_methods": SectionBase(
                title="Methods",
                order=2,
                text="We conducted a retrospective study...",
                subsections={
                    "2.1_data": SectionBase(
                        title="Data Collection",
                        order=1,
                        text="Chest X-rays were collected from 5 hospitals...",
                    ),
                    "2.2_model": SectionBase(
                        title="Model Architecture",
                        order=2,
                        text="We used a ResNet-50 architecture...",
                    ),
                },
            ),
        },
    ),
)

# Export to MongoDB
mongo_doc = doc.model_dump(by_alias=True)
# Use mongo_doc with pymongo or motor
```

## Creating a Regulatory Document

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
        title="AI-Chest Scanner 510(k) Summary - K240001",
        k_number="K240001",
        clearance_date=date(2024, 8, 15),
        applicant="Medical AI Corporation",
        device_name="AI-Chest Scanner v2.0",
        device_class="II",
        product_code="MYN",
        clinical_domain="radiology",
        tags=["510k", "ai", "radiology"],
    ),
)

# Add predicate device
doc.content.predicate_device = PredicateDeviceInfo(
    k_number="K190123",
    device_name="ChestView AI System",
    manufacturer="Competitor Medical Inc",
    comparison_summary="Similar intended use for chest X-ray analysis with AI",
)

# Add sections
doc.content.sections["1_intended_use"] = SectionBase(
    title="Intended Use",
    order=1,
    text="The AI-Chest Scanner is intended for analysis of chest radiographs...",
)

doc.content.sections["2_device_description"] = SectionBase(
    title="Device Description",
    order=2,
    text="The device is a software-only solution...",
)
```

## Creating an AI System Card

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

## Inserting into MongoDB

```python
from motor.motor_asyncio import AsyncIOMotorClient
from ashmatics_datamodels.documents import EvidenceDocument

# Create document
doc = EvidenceDocument(
    _id="evidence-001",
    metadata_content=EvidenceMetadataContent(...),
)

# MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.ashmatics_kb
collection = db.kb_evidence_doc

# Insert
result = await collection.insert_one(doc.model_dump(by_alias=True))
print(f"Inserted document: {result.inserted_id}")
```

## Querying Documents

```python
from motor.motor_asyncio import AsyncIOMotorClient
from ashmatics_datamodels.documents import (
    EvidenceDocument,
    EvidenceSummary,
)

client = AsyncIOMotorClient("mongodb://localhost:27017")
collection = client.ashmatics_kb.kb_evidence_doc

# Query by clinical domain
async def get_radiology_papers():
    cursor = collection.find({
        "metadata_content.clinical_domain": "radiology",
        "metadata_content.publication_date": {"$gte": "2024-01-01"}
    })

    summaries = []
    async for doc in cursor:
        # Parse full document
        evidence = EvidenceDocument(**doc)
        # Create summary
        summary = EvidenceSummary.from_document(evidence)
        summaries.append(summary)

    return summaries

# Get summaries (lighter weight)
async def get_evidence_summaries(limit=10):
    cursor = collection.find(
        {},
        {
            "_id": 1,
            "metadata_content.title": 1,
            "metadata_content.authors": 1,
            "metadata_content.journal": 1,
            "metadata_content.publication_date": 1,
            "metadata_object.created_at": 1,
        }
    ).limit(limit)

    return await cursor.to_list(length=limit)
```

## Full-Text Search

```python
# Create text index
await collection.create_index([
    ("metadata_content.title", "text"),
    ("metadata_content.abstract", "text"),
    ("metadata_content.keywords", "text"),
])

# Search
async def search_evidence(query: str):
    cursor = collection.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})])

    results = []
    async for doc in cursor:
        results.append(EvidenceDocument(**doc))

    return results

# Usage
papers = await search_evidence("deep learning pneumonia")
```

## Aggregation Pipeline

```python
# Count papers by clinical domain
async def count_by_domain():
    pipeline = [
        {"$group": {
            "_id": "$metadata_content.clinical_domain",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]

    cursor = collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)
    return results

# Get papers per year
async def papers_per_year():
    pipeline = [
        {"$group": {
            "_id": {"$year": "$metadata_content.publication_date"},
            "count": {"$sum": 1},
            "domains": {"$addToSet": "$metadata_content.clinical_domain"}
        }},
        {"$sort": {"_id": -1}}
    ]

    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)
```

## Updating Documents

```python
from datetime import datetime, timezone

# Update metadata
result = await collection.update_one(
    {"_id": "evidence-001"},
    {
        "$set": {
            "metadata_object.updated_at": datetime.now(timezone.utc),
            "metadata_content.tags": ["radiology", "ai", "pneumonia", "updated"]
        }
    }
)

print(f"Modified: {result.modified_count}")
```

## Batch Insert with Validation

```python
from ashmatics_datamodels.documents import EvidenceDocument
from pydantic import ValidationError

async def batch_insert_evidence(papers: list[dict]):
    """Insert evidence documents with validation."""
    valid_docs = []
    errors = []

    for paper_data in papers:
        try:
            doc = EvidenceDocument(**paper_data)
            valid_docs.append(doc.model_dump(by_alias=True))
        except ValidationError as e:
            errors.append({
                "data": paper_data,
                "error": str(e)
            })

    if valid_docs:
        result = await collection.insert_many(valid_docs)
        print(f"Inserted {len(result.inserted_ids)} documents")

    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors:
            print(err)

    return len(valid_docs), len(errors)
```

## Document Versioning

```python
from ashmatics_datamodels.documents import EvidenceDocument

# Create new version
doc = await collection.find_one({"_id": "evidence-001"})
evidence = EvidenceDocument(**doc)

# Increment version
current_version = evidence.metadata_object.version
new_version = f"{int(float(current_version)) + 1}.0"

# Update
await collection.update_one(
    {"_id": "evidence-001"},
    {
        "$set": {
            "metadata_object.version": new_version,
            "metadata_object.updated_at": datetime.now(timezone.utc),
        }
    }
)
```
