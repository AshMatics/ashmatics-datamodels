# Copyright 2026 Asher Informatics PBC
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
AI System Registry rule vocabularies (ASHFORGE-412, ADR-036 §2.5).

The canonical home of the vocabularies the AI System Registry writes and the
governance rule files read. Downstream mirrors (coreapp Django TextChoices,
frontend aiRegistryTaxonomies.ts) pin to these via parity tests.

Usage::

    from ashmatics_datamodels.registry import (
        RegistryCategory,
        RegistryAIType,
        RegistrySourcing,
        RegistryDeployment,
        is_clinical_use,
    )
"""

from .bindings import REGISTRY_BINDINGS, BindingStatus, SchemeBinding
from .derive import (
    is_clinical_use,
    org_sourcing_mix,
    portfolio_size_bucket,
    sourcing_obligation,
)
from .enums import (
    DeploymentStatus,
    OrgSourcingMix,
    PortfolioSizeBucket,
    RegistryAIType,
    RegistryCategory,
    RegistryDeployment,
    RegistrySourcing,
    SourcingChannel,
)

__all__ = [
    "RegistryCategory",
    "RegistryAIType",
    "RegistrySourcing",
    "SourcingChannel",
    "RegistryDeployment",
    "DeploymentStatus",
    "PortfolioSizeBucket",
    "OrgSourcingMix",
    "is_clinical_use",
    "portfolio_size_bucket",
    "org_sourcing_mix",
    "sourcing_obligation",
    "REGISTRY_BINDINGS",
    "BindingStatus",
    "SchemeBinding",
]
