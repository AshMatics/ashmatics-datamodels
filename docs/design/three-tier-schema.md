# Three-Tier Document Schema

Design rationale for the MongoDB three-tier document structure.

## Overview

All `kb_*` MongoDB collections follow a standardized three-tier structure:

```
MongoDocumentBase
├── Tier 1: metadata_object    (Artifact/file metadata)
├── Tier 2: metadata_content   (Content classification)
└── Tier 3: content            (Document body)
```

## Design Rationale

### Separation of Concerns

Each tier serves a distinct purpose:

- **Tier 1 (metadata_object)** - "When and how was this stored?"
  - Provenance and versioning
  - Storage and processing information
  - System-level metadata

- **Tier 2 (metadata_content)** - "What is this content about?"
  - Content classification
  - Searchable metadata
  - Indexing and filtering fields

- **Tier 3 (content)** - "What does it say?"
  - Actual document body
  - Hierarchical sections
  - Figures, tables, references

### Benefits

#### 1. Consistent Queries
All collections have the same top-level structure:

```javascript
// Find recent evidence papers
db.kb_evidence_doc.find({
  "metadata_content.clinical_domain": "radiology",
  "metadata_object.created_at": {"$gte": ISODate("2024-01-01")}
})

// Find 510(k) summaries
db.kb_regulatory_doc.find({
  "metadata_content.content_type": "510k_summary",
  "metadata_content.clearance_date": {"$gte": "2024-01-01"}
})
```

#### 2. Efficient Search
Filter on metadata without loading full content:

```javascript
// List view - only metadata
db.kb_evidence_doc.find(
  {"metadata_content.clinical_domain": "radiology"},
  {
    "metadata_content.title": 1,
    "metadata_content.authors": 1,
    "metadata_object.created_at": 1
  }
)
```

#### 3. Flexible Content
Different document types extend base content:

```python
# Evidence has study-specific fields
class EvidenceContent(ContentBase):
    study_design: Optional[str]
    sample_size: Optional[int]

# Regulatory has predicate device
class RegulatoryContent(ContentBase):
    predicate_device: Optional[PredicateDeviceInfo]
```

#### 4. Clean Separation
Storage details don't pollute business logic:

```python
# Tier 1: System concerns
metadata_object.storage_location  # Where is the PDF?
metadata_object.processing_pipeline  # How was it processed?

# Tier 2: Business concerns
metadata_content.clinical_domain  # What specialty?
metadata_content.publication_date  # When published?

# Tier 3: Content
content.sections  # What does it say?
```

## Structure Details

### Tier 1: metadata_object

```python
MetadataObjectBase(
    # Provenance
    created_at: datetime
    updated_at: datetime
    created_by: str
    version: str

    # Storage
    storage_location: Optional[str]
    file_size_bytes: Optional[int]
    checksum_md5: Optional[str]
    original_filename: Optional[str]

    # Processing
    processing_pipeline: Optional[str]
    processing_completed_at: Optional[datetime]
    processing_errors: list[str]
)
```

### Tier 2: metadata_content

```python
MetadataContentBase(
    # Classification
    document_type: DocumentType
    content_type: ContentType

    # Searchable
    title: str
    abstract: Optional[str]
    keywords: list[str]
    tags: list[str]

    # Categorization
    clinical_domain: Optional[str]
    language: str
)
```

Extended by type-specific metadata:
- `EvidenceMetadataContent` - authors, journal, DOI
- `RegulatoryMetadataContent` - K number, device class
- `SystemCardMetadataContent` - system name, version, release date (HTI-1 Model Summary)
- `IfuMetadataContent` - catalogue number, product and manufacturer as written
- etc.

### Tier 3: content

```python
ContentBase(
    # Hierarchical structure
    sections: dict[str, SectionBase]

    # Rich media
    figures: list[FigureReference]
    tables: list[TableReference]

    # Citations
    references: list[CitationReference]
)
```

Extended by type-specific content:
- `EvidenceContent` - study design, sample size
- `RegulatoryContent` - predicate device
- `SystemCardContent` - monitoring rows, model parts
- etc.

## Example Document

```python
{
  "_id": "evidence-2024-001",

  "metadata_object": {
    "created_at": "2024-11-21T10:00:00Z",
    "updated_at": "2024-11-21T10:00:00Z",
    "created_by": "ingestion-pipeline",
    "version": "1.0",
    "storage_location": "s3://kb/papers/smith2024.pdf",
    "file_size_bytes": 2048000,
    "processing_pipeline": "grobid_v0.7.2"
  },

  "metadata_content": {
    "document_type": "kb_evidence_doc",
    "content_type": "peer_reviewed_paper",
    "title": "Deep Learning for Pneumonia Detection",
    "authors": ["Dr. Smith", "Dr. Doe"],
    "journal": "Radiology: AI",
    "doi": "10.1148/ryai.2024123456",
    "publication_date": "2024-03-15",
    "clinical_domain": "radiology",
    "keywords": ["deep learning", "pneumonia"],
    "tags": ["ai", "radiology"]
  },

  "content": {
    "sections": {
      "1_introduction": {
        "title": "Introduction",
        "order": 1,
        "text": "Pneumonia is a leading cause..."
      }
    },
    "figures": [],
    "tables": [],
    "references": []
  }
}
```

## Indexing Strategy

### Recommended Indexes

```javascript
// Evidence documents
db.kb_evidence_doc.createIndex({
  "metadata_content.clinical_domain": 1,
  "metadata_content.publication_date": -1
})

db.kb_evidence_doc.createIndex({
  "metadata_content.title": "text",
  "metadata_content.abstract": "text",
  "metadata_content.keywords": "text"
})

// Regulatory documents
db.kb_regulatory_doc.createIndex({
  "metadata_content.k_number": 1
})

db.kb_regulatory_doc.createIndex({
  "metadata_content.clearance_date": -1
})
```

## Querying Patterns

### List View (Metadata Only)
```python
cursor = collection.find(
    {"metadata_content.clinical_domain": "radiology"},
    {
        "_id": 1,
        "metadata_content.title": 1,
        "metadata_content.authors": 1,
        "metadata_object.created_at": 1
    }
).limit(20)
```

### Detail View (Full Document)
```python
doc = collection.find_one({"_id": "evidence-001"})
evidence = EvidenceDocument(**doc)
```

### Search (Text Index)
```python
cursor = collection.find(
    {"$text": {"$search": "pneumonia deep learning"}},
    {"score": {"$meta": "textScore"}}
).sort([("score", {"$meta": "textScore"})])
```

## Migration from Flat Structure

If migrating from a flat structure:

```python
# Old flat structure
{
  "_id": "doc-001",
  "title": "Paper Title",
  "created_at": "2024-01-01",
  "storage_path": "s3://...",
  "clinical_domain": "radiology",
  "content_text": "Full paper text..."
}

# New three-tier structure
{
  "_id": "doc-001",
  "metadata_object": {
    "created_at": "2024-01-01",
    "storage_location": "s3://..."
  },
  "metadata_content": {
    "title": "Paper Title",
    "clinical_domain": "radiology"
  },
  "content": {
    "sections": {
      "1_full_text": {
        "title": "Full Text",
        "order": 1,
        "text": "Full paper text..."
      }
    }
  }
}
```

## Related Documents

- [Migration Plan](migration-plan.md)
- [MongoDB Documents Examples](../examples/mongodb-documents.md)
