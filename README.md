# AshMatics Core DataModels

**Version: 0.3.0**

Canonical Pydantic data models for AshMatics healthcare applications.

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
