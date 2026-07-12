# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **ashmatics-core-datamodels**, a canonical Pydantic data models library for the AshMatics healthcare ecosystem. It serves as the single source of truth for data contracts across:
- Ashmatics Knowledge Base (KB)
- ashmatics-tools SDK
- ashmatics-knowledgebase-tools (ingestion pipelines)
- AI Watch applications

Version: 0.7.0 as of 2026-07-12 — `pyproject.toml` and the README changelog are authoritative, not this line.

## Development Commands

### Environment Setup
```bash
# Python 3.11+ required; uv-managed venv (no pip)
uv venv .venv
VIRTUAL_ENV="$(pwd)/.venv" uv pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
.venv/bin/python -m pytest

# Run with coverage
.venv/bin/python -m pytest --cov=src/ashmatics_datamodels --cov-report=term-missing

# Run specific test file
.venv/bin/python -m pytest tests/fda/test_clearances.py

# Run specific test
.venv/bin/python -m pytest tests/fda/test_clearances.py::TestFDA510kClearance::test_k_number_validation
```

### Linting and Type Checking
```bash
# Lint with ruff
uv run --with ruff ruff check src/

# Format code
uv run --with ruff ruff format src/ tests/

# Type check with mypy
.venv/bin/python -m mypy src/
```

### Building the Package
```bash
# Build sdist + wheel
uv build

# Install locally in editable mode
VIRTUAL_ENV="$(pwd)/.venv" uv pip install -e .
```

### Documentation
```bash
# Install documentation dependencies
uv pip install -e ".[docs]"

# Serve docs locally (auto-reload on changes)
uv run mkdocs serve
# Open http://127.0.0.1:8000

# Build static documentation site
uv run mkdocs build
# Output in site/
```

## Architecture

### Module Organization

The library follows a domain-driven structure:

- **common/** - Cross-jurisdictional base models, validators, enums
  - `base.py`: `AshMaticsBaseModel`, `TimestampedModel`, `AuditedModel`
  - `validators.py`: Shared validators (ISO dates, country codes, FDA identifiers)
  - `enums.py`: Global enums (`AuthorizationStatus`, `RegulatoryStatus`, `RiskCategory`)
  - `regulators.py`: Multi-jurisdiction regulator schemas
  - `frameworks.py`: Regulatory framework schemas (FDA, EMA, etc.)

- **fda/** - FDA-specific schemas aligned with OpenFDA API
  - `manufacturers.py`: FDA manufacturer schemas
  - `clearances.py`: 510(k), PMA, De Novo clearance schemas
  - `classifications.py`: Product codes, device classifications
  - `products.py`: Product and regulatory status schemas
  - `recalls.py`: FDA recall schemas
  - `adverse_events.py`: MAUDE adverse event schemas

- **use_cases/** - Clinical AI use case taxonomy
  - `categories.py`: Use case category hierarchy
  - `use_cases.py`: Use case schemas with evidence links

- **documents/** - MongoDB three-tier document structure
  - `base.py`: Base classes for all `kb_*` collections
  - `evidence.py`: Evidence/publication documents
  - `regulatory.py`: Regulatory document schemas (510k summaries)
  - `models.py`: AI model card documents
  - `products.py`: Product profile cards
  - `manufacturers.py`: Manufacturer profile cards
  - `use_cases.py`: Clinical use case documents

- **org/** - FORGE-aligned organization-instance shape (JAC-27)
  - `enums.py`: Org governance-boundary vocabulary (`ParentRelationship`, `GovernanceAutonomy`, `UnitGranularity`)
  - `organization.py`: `OrganizationModel` — prototype of the ADR-002 `x_ontology_*` binding convention

- **methods/** - CHAR governance-method contracts (aigov-framework ADR-011; ASHKBAPP-99)
  - `MethodDefinition`, `ApplicabilityProfile`, `MethodSet`, `ApprovedMethodSet`, `MethodRegistry`
  - CLF rule-grammar types shared with coreapp; ontology-bound enums guarded by rdflib tests

- **artifacts/** - aigov-framework ADR-006 artifact-plane contracts (ASHKBAPP-99)
  - `base_content.py`: KB base-content side (`ToolRef`, `PracticeView`, `BaseArtifact`, `CompiledView`)
  - `instances.py`: tenant-instantiation side (`DecisionRecord`, `ExportRecord`, `InstanceArtifact`, `InstanceIndex`)

- **utils/** - Parsing and normalization utilities (future)

Ontology-bound enums across `documents/`, `org/`, and `methods/` carry `x_ontology_scheme` bindings validated by rdflib guard tests against `../ashmatics-ontology` TTLs (ADR-002 in that repo's `docs/decisions/` — this repo has no ADR series of its own).

### Three-Tier MongoDB Document Pattern

All `kb_*` collection documents follow this standardized structure:

**Tier 1: metadata_object** - Artifact/file metadata (provenance, versioning, storage)
**Tier 2: metadata_content** - Content classification metadata (search, filtering)
**Tier 3: content** - Actual document body (sections, figures, tables, references)

Example:
```python
from ashmatics_datamodels.documents import EvidenceDocument, EvidenceMetadataContent

doc = EvidenceDocument(
    _id="evidence-123",
    metadata_object=MetadataObjectBase(  # Tier 1
        storage_location="s3://kb/papers/file.pdf",
        processing_pipeline="grobid_v0.7.2"
    ),
    metadata_content=EvidenceMetadataContent(  # Tier 2
        document_type=DocumentType.EVIDENCE_DOC,
        title="AI in Radiology",
        clinical_domain="radiology"
    ),
    content=ContentBase(  # Tier 3
        sections={"1_intro": SectionBase(title="Introduction", order=1)}
    )
)
```

See `src/ashmatics_datamodels/documents/base.py` for full implementation.

### Validation Philosophy

- **Strict validation**: Validators raise `ValueError` on invalid input (prefer fail-fast)
- **Normalization**: Auto-uppercase codes (K numbers, product codes, country codes)
- **Format checking**: Regex validation for FDA identifiers (K######, P######, product codes)
- **Type safety**: Full Pydantic v2 type hints for IDE support

Example validators:
- `validate_k_number_format()`: Validates K######/BK######/DEN###### format
- `validate_product_code()`: Validates 3-letter FDA product codes
- `validate_iso_date()`: Parses YYYY-MM-DD or MM/DD/YYYY dates

### OpenFDA Alignment

FDA schemas mirror OpenFDA API response structures for easy data ingestion:
- Field names match OpenFDA JSON keys
- Enums align with OpenFDA terminology
- Date formats support both ISO 8601 and US formats

## Key Design Patterns

### Base Model Inheritance
All models inherit from `AshMaticsBaseModel` which provides:
- `model_config = ConfigDict(use_enum_values=True, validate_assignment=True)`
- Common serialization/deserialization behavior
- Consistent JSON export with `model_dump(by_alias=True)`

### Timestamped Models
Use `TimestampedModel` for models requiring automatic timestamp tracking:
```python
class MyModel(TimestampedModel):
    name: str
    # created_at and updated_at auto-generated
```

### Document Summaries
Each document type has a corresponding summary schema for list views:
```python
summary = EvidenceSummary.from_document(full_document)
# Flattens three-tier structure for efficient API responses
```

## Migration Status (Phase Tracking)

**Phase 1 (v0.1.0)** ✅ COMPLETE:
- FDA core schemas (manufacturers, clearances, classifications, products)
- Use case base schemas
- Common validators and enums
- Regulators and frameworks

**Phase 2 (v0.2.0)** ✅ COMPLETE:
- MongoDB document schemas (three-tier structure)
- Evidence and regulatory documents
- Model cards, product cards, manufacturer cards

**Beyond the original phase plan** — releases are tracked in the README changelog (authoritative):
- 0.4.0: `org/` module (JAC-27)
- 0.5.0: ontology-bound document vocabularies (ASHKBAPP-91)
- 0.6.0: `methods/` module (ASHKBAPP-99; never separately released)
- 0.7.0: `artifacts/` module (ASHKBAPP-99)

**Future Phases**:
- Phase 3: Ontology consolidation (terms, valuesets from ashmatics-tools)
- Phase 4: Evidence quality metrics
- Phase 5: Multi-jurisdiction (EMA, PMDA)

See `docs/Plans/ENGR-DesignPlan-CompleteDataModels-2025-11-21.md` for the original migration plan.

## Important Constraints

1. **No ORM coupling**: These are pure Pydantic models, no SQLAlchemy/Beanie dependencies
2. **No business logic**: Models define structure and validation only
3. **Database agnostic**: Work with any backend (MongoDB, PostgreSQL, etc.)
4. **No auto-generated IDs**: Applications manage ID generation
5. **Apache 2.0 licensing**: All files must include license header

## Testing Standards

- Test files mirror source structure: `tests/fda/test_clearances.py` → `src/ashmatics_datamodels/fda/clearances.py`
- Use pytest fixtures for common test data
- Test validation edge cases (invalid K numbers, out-of-range dates)
- Test JSON serialization roundtrips
- Test summary generation from full documents

## Consumer Applications

When making changes, consider impact on:
- **KB FastAPI**: Uses these schemas for request/response validation
- **ashmatics-knowledgebase-tools**: DocLing pipelines validate against these before API calls
- **ashmatics-tools**: Will consolidate ontology schemas here

## Version Bumping

Follow semantic versioning:
- Patch (0.X.Y): Bug fixes, clarifications
- Minor (0.X.0): New schemas, backward-compatible additions
- Major (X.0.0): Breaking changes to existing schemas

Update both `pyproject.toml` version and `src/ashmatics_datamodels/__init__.py` `__version__`.

---

## Release & versioning

Conventions live in `ashmatics-engineering` ("the Asher Way") — treat as authoritative.

- **Tags:** `<sku>/vMAJOR.MINOR.PATCH` — e.g. `lcr/v1.0.0`. SKU is a path-like prefix.
- **Branching:** trunk-based. No `release/*` branches in this repo.
- **Package SemVer** (bumped in `pyproject.toml` + `__init__.py` per the Version Bumping section above) is this library's own version. FORGE platform release alignment is handled separately via the manifest in `ashmatics-infra/release-manifests/`.
