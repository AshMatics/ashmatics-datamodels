# AshMatics Core DataModels

**Version: 0.7.0**

Canonical Pydantic data models for AshMatics healthcare applications.

## Changelog

### v0.7.0 (2026-07-12) — ASHKBAPP-99
- Added the `artifacts` module: the aigov-framework ADR-006 artifact plane, ported field-for-field from that repo's legacy `models_pydantic/pydantic_models.py` (now a deprecation shim over this module). KB base-content side: `ToolRef`, `PracticeView`, `BaseArtifact`, `CompiledView`; coreapp tenant-instantiation side: `DecisionRecord`, `ExportRecord`, `InstanceArtifact`, `InstanceIndex`.
- `InstanceArtifact` carries the one clean ontology binding (`x_ontology_class: ashcai:WorkProduct`), guard-checked against the TTL. Fuller bindings (e.g. `BaseArtifact.type` vs `ash:DocumentKindScheme`) deferred to the ADR-002 promotion gate — different stored values make that a redesign, not a port.
- Behavior tightening vs the legacy plain `BaseModel`: extra fields forbidden, assignment validation (house `AshMaticsBaseModel`). A field-parity test pins the port against the legacy shape.

### v0.6.0 (2026-07-12) — ASHKBAPP-99
- Added the `methods` module: CHAR governance-method contracts per aigov-framework ADR-011 §5. `MethodDefinition` / `ApplicabilityProfile` / `EvidenceRef` / `DefaultRule` model `method_registry.yaml` field-for-field; `MethodSet` / `ApprovedMethodSet` carry the shared-set and Blueprint-resolved shapes; `MethodRegistry` round-trips the whole registry document without loss (acceptance-tested against the live file).
- `ApplicabilityProfile` axes are `x_ontology_scheme`-bound enums against the five ash facet schemes plus the new `ash:ModelClassScheme` (ontology ADR-006), each also carrying its `ashcai:methodAppliesTo` subproperty via `x_ontology_property`. Values use concept local names (`ap-predictive`), the canonical CHAR concept IDs.
- CLF v0.6.0 rule-grammar types shared with coreapp MethodRoute (ADR-031): `ConditionScope`, `EvaluationTime`, `MethodControlAction`, `SystemAttribute`.
- New ADR-002 rdflib binding guard (`tests/methods/test_ontology_binding.py`): accepts concept local names in addition to notations/prefLabels (the CHAR ID convention), and adds a reverse-completeness check so facet-scheme concepts without enum members also fail CI. This supersedes the static SKOS snapshot in the aigov-framework's `validate_method_registry.py`.
- ID grammars exported as constants (`METHOD_ID_PATTERN`, `JUNCTION_REF_PATTERN`, ...) so framework validators import one truth.
- Requires `ashmatics-ontology >= 2.2.0` (`GovernanceMethodScheme`, `ModelClassScheme`).
- Deliberately NOT included: the aigov-framework's legacy `models_pydantic/pydantic_models.py` reconciliation — a separate PR per the Phase 2 handoff (no new contracts land in that file).

### v0.5.0 (2026-07-11) — ASHKBAPP-91
- `DocumentType` (the `kb_documents` `document_type` discriminator) is now the KIND axis, single-sourced from the ontology `ash:DocumentKindScheme` (ADR-002 Decision 5). Added `GENERAL` (`kb_general`) fallback; `USE_CASE` kept but **deprecated** (ADR-005 — the Mongo use-case path is retired to the Postgres `kb_use_cases` spine).
- New `RegulatoryRegion` (8) and `RegulatoryPathway` (7) enums, ontology-bound to `ash:RegulatoryRegionScheme` / `ash:RegulatoryPathwayScheme`; added optional `regulatory_region` / `regulatory_pathway` fields to `RegulatoryMetadataContent` (regulator scoping carried as sibling fields — the "split" model).
- Extended the ADR-002 rdflib binding guard to the document models (`tests/documents/test_ontology_binding.py`): every scheme-bound enum value must be a real concept in its scheme, so vocabulary drift fails tests.
- Requires `ashmatics-ontology >= 2.1.0` (`DocumentKindScheme`).

### v0.4.0 (2026-06-02) — JAC-27
- Added the `org` module: FORGE-aligned organization-instance shape, with `x_ontology_scheme` bindings to the `forge:` ontology and the initial ADR-002 rdflib binding guard (`tests/org/test_ontology_binding.py`). Committed but never separately released to PyPI; first shipped in 0.5.0.

### v0.3.1 (2026-01-25) — ASHKBAPP-66
- Added `PROCESS_DOCUMENTATION` to `GovernanceCategory` enum
- This is a core CAI framework category required for MCP service compatibility

## Overview

This library provides the **single source of truth** for data contracts across the AshMatics ecosystem:
- Knowledge Base (KB)
- CoreApp
- ashmatics-tools SDK
- AI Watch applications

## Features

- **FDA Vocabulary**: OpenFDA-aligned schemas for manufacturers, clearances, classifications, recalls, adverse events
- **MongoDB Document Schemas**: Three-tier structure for all `kb_*` collections (evidence, regulatory, model cards, products, manufacturers, use cases)
- **Governance Document Models**: Clinical AI Governance Framework artifacts (policies, SOPs, work products, process documentation)
- **Use Case Taxonomy**: Clinical AI use case categorization
- **Rich Validation**: Built-in validators for regulatory identifiers (K numbers, product codes)
- **Database Agnostic**: Pure Pydantic models, no ORM coupling
- **Type Safe**: Full type hints with mypy support

## Installation

```bash
# From git (recommended for now)
pip install git+https://github.com/AsherInformatics/ashmatics-core-datamodels.git

# Or add to pyproject.toml
# dependencies = [
#     "ashmatics-datamodels @ git+https://github.com/AsherInformatics/ashmatics-core-datamodels.git",
# ]
```

## Quick Start

```python
from ashmatics_datamodels.fda import (
    FDA_ManufacturerBase,
    FDA_510kClearance,
    FDA_DeviceClass,
    ClearanceType,
)

# Create a manufacturer
manufacturer = FDA_ManufacturerBase(
    manufacturer_name="Medical AI Corp",
    applicant="Medical AI Corp",
)

# Create a 510(k) clearance with validation
clearance = FDA_510kClearance(
    k_number="K240001",  # Validated format
    clearance_date="2024-08-15",
    device_name="AI-Chest Scanner",
    device_class=FDA_DeviceClass.CLASS_2,
)
```

## Package Structure

```
ashmatics_datamodels/
├── common/          # Base models, validators, regulators, frameworks
├── fda/             # FDA vocabulary (manufacturers, clearances, classifications, recalls, adverse events)
├── documents/       # MongoDB document schemas (three-tier structure)
├── use_cases/       # Clinical AI use case taxonomy
└── utils/           # Parsing and normalization utilities
```

## Documentation

📚 **[Full Documentation](https://asherinformatics.github.io/ashmatics-core-datamodels/)** (when published)

Or build locally:
```bash
uv pip install -e ".[docs]"
uv run mkdocs serve
```

### Design Documents
- [Phase 1: FDA & Common Schemas](docs/IMPL-CommonDataModel_Phase1-2025-11-21.md)
- [Phase 2: MongoDB Document Schemas](docs/IMPL-MongoDocumentSchemas-Phase2-2025-11-21.md)
- [Complete Migration Plan](docs/Plans/ENGR-DesignPlan-CompleteDataModels-2025-11-21.md)

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

This is an internal Asher Informatics library. For questions, contact info@asherinformatics.com.
