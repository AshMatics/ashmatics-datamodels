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
Organization governance-boundary models (FORGE-aligned).

The customer/organization layer of the data-model contract (ADR-002): the shared
shape of a customer org's governance boundary, annotated to the FORGE ontology.

Usage::

    from ashmatics_datamodels.org import (
        OrganizationModel,
        ParentRelationship,
        GovernanceAutonomy,
        UnitGranularity,
        ApprovedSiteRoleSet,
        SiteRole,
    )
"""

from .enums import (
    GovernanceAutonomy,
    ParentRelationship,
    ProviderOrgType,
    SiteOfCare,
    UnitGranularity,
)
from .organization import OrganizationModel
from .site_roles import (
    ApprovedSiteRoleSet,
    SiteRole,
    SiteRoleAdjustment,
    SiteRoleHolder,
    SiteRoleHolderKind,
)

__all__ = [
    "OrganizationModel",
    "ProviderOrgType",
    "SiteOfCare",
    "ParentRelationship",
    "GovernanceAutonomy",
    "UnitGranularity",
    # site roles (ADR-057)
    "ApprovedSiteRoleSet",
    "SiteRole",
    "SiteRoleAdjustment",
    "SiteRoleHolder",
    "SiteRoleHolderKind",
]
