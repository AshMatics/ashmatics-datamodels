# AshMatics Core DataModels

**Version: 0.8.1**

Canonical Pydantic data models for AshMatics healthcare applications.

## Changelog

### v0.8.1 (2026-08-13) — ASHFORGE-536
- `RegistryDeployment` gains three values for admin/operational systems: `ehr`, `enterprise_system`, `agentic_platform` — inserted before `platform` in the device→cloud order (SRS-REG-03). Same PRODUCT binding tier as the rest of the enum (deliberately unbound to ash:).

### v0.8.0 (2026-08-03) — ASHFORGE-412
- Added the `registry` module: the AI System Registry rule vocabularies (ADR-036 §2.5) — `RegistryCategory`, `RegistryAIType`, `RegistrySourcing`, `RegistryDeployment` — the canonical home that coreapp's Django `TextChoices` and the frontend's `aiRegistryTaxonomies.ts` pin to by parity test. Every value is a rule-engine key; changing one is a vocabulary decision, not a rename (SRS-REG-AC-6).
- AC-2 resolved: SRS-REG-03's `clinical_use` boolean is DERIVED (`is_clinical_use`), never stored — the stored value is the three-way category. The decision test lives in the `RegistryCategory` docstring: does the system's output assert something about an individual patient's condition or care?
- AC-3 resolved: the org-level typed questions retire; `PortfolioSizeBucket` and `OrgSourcingMix` survive as derived vocabularies (`portfolio_size_bucket` from the active-entry count, `org_sourcing_mix` rolling per-system sourcing up with hybrid counting half).
- Ontology anchoring declared in a `SchemeBinding` table (`registry/bindings.py`) with a three-state status (BOUND / PENDING / PRODUCT) and enforced by an rdflib guard: `RegistryAIType` is BOUND to `ash:AIParadigmScheme` by `skos:notation` (`other` carved out as a deliberate UI collapse of the finer paradigms — the guard also fails if a carved-out value later gains a concept); `RegistryCategory` is PENDING the clinical/operational/administrative scope-zone triad + `ash:OperationalPurposeScheme` being authored in ashmatics-ontology (skips loudly in CI until it lands); sourcing, deployment, and the derived vocabularies are recorded PRODUCT so "unanchored" is always a decision, never an oversight.
- Interop note: this module binds by `skos:notation` (`predictive`) while the `methods` module binds by concept local name (`ap-predictive`). The mapping is mechanical (`ap-` + notation) but rule authors bridging registry systems to CHAR method applicability must map, not string-compare.
- Ontology v2.3.0 / ADR-007 landed mid-story (ASHFORGE-436) and this release consumes it (guards require `ashmatics-ontology >= 2.3.0`): `RegistryCategory` is now BOUND to `ash:ScopeZoneScheme` (the ontology allows multi-zone systems; the registry stores one primary zone — additive to widen later). New `DeploymentStatus` enum BOUND to `ash:DeploymentStatusScheme` (per-deployment lifecycle on the `forge:deploysApplication` edge; distinct from `RegistryDeployment` topology, and from coreapp's minimal active/retired entry status). New `org.ProviderOrgType` enum BOUND to `ash:SemanticType_T093`, tightening `OrganizationModel.organization_type` from bare `str` — coreapp emits `None` there today, so nothing breaks; mapping coreapp's legacy org-type values is the unblocked follow-up. (Named `ProviderOrgType`, not the handover's `OrganizationType`, because coreapp already has an unrelated `OrganizationType` TextChoices — a platform-actor/access-control axis with zero value overlap.)
- Sourcing resolved (decision 2026-08-03): the ontology's `ash:SourcingScheme` (commercial / ehr_embedded / homegrown / research) is an acquisition-channel axis, not the obligation triad. The channel is what the customer answers, so new `SourcingChannel` is the STORED per-entry field, BOUND to the scheme; the SRS-REG-15a obligation triad (`RegistrySourcing`) becomes DERIVED via `sourcing_obligation()` (commercial/ehr_embedded → vendor, homegrown/research → in_house, `locally_adapted=True` on a vendor channel → hybrid). Same stored-fact/derived-judgment philosophy as `clinical_use`. Downstream: coreapp's sourcing picker and SRS-REG-15a wording must move to channel values (dev-only data so far).
- NOT bound, deliberately: `ash:OperationalPurposeScheme` — explicitly a seed vocabulary, nothing consumes purpose yet (note its `prior_authorization_ops` notation is distinct from the clinical scheme's `prior_authorization`).

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
- Committed but never separately released to PyPI; first shipped in 0.7.0.

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
