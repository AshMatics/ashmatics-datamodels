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

"""Tests for the OrganizationModel governance-boundary shape (JAC-27)."""

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.org import (
    GovernanceAutonomy,
    OrganizationModel,
    ParentRelationship,
    UnitGranularity,
)


class TestOrganizationModelDefaults:
    def test_minimal_org_uses_safe_defaults(self):
        org = OrganizationModel(organization_id="org-001", name="Standalone Clinic")
        # A standalone org: no edges, holds its own governance.
        assert org.parent_relationship == ParentRelationship.NONE
        assert org.governance_autonomy == GovernanceAutonomy.AUTONOMOUS
        assert org.parent_id is None
        assert org.governed_by_id is None
        assert org.unit_granularity is None
        assert org.shares_ccn_with_parent is False

    def test_config_merges_base_and_ontology_class(self):
        # Pydantic must MERGE the base config (extra=forbid) with the subclass's
        # json_schema_extra — if it replaced, extra would revert to 'ignore'.
        config = OrganizationModel.model_config
        assert config.get("extra") == "forbid"
        assert config.get("use_enum_values") is True
        assert config["json_schema_extra"]["x_ontology_class"] == "forge:Organization"


class TestGovernanceBoundaryShapes:
    def test_provider_based_facility_inherits_governance(self):
        # Provider-based facility: structure edge = providerBasedTo, governance
        # inherited from the parent, shares CCN.
        org = OrganizationModel(
            organization_id="fac-imaging-7",
            name="Downtown Imaging Center",
            parent_id="hosp-001",
            parent_relationship=ParentRelationship.PROVIDER_BASED,
            governed_by_id="hosp-001",
            governance_autonomy=GovernanceAutonomy.INHERITED,
            unit_granularity=UnitGranularity.SECTION,
            specialty="ash:RadiologyConcept",
            shares_ccn_with_parent=True,
            cms_ccn="123456",
        )
        assert org.governance_autonomy == GovernanceAutonomy.INHERITED
        assert org.shares_ccn_with_parent is True
        assert org.governed_by_id == "hosp-001"

    def test_affiliated_org_owns_its_governance(self):
        # Affiliated = owned by a parent corporately, but governs itself.
        org = OrganizationModel(
            organization_id="grp-cardio",
            name="Affiliated Cardiology Group",
            parent_id="mso-001",
            parent_relationship=ParentRelationship.AFFILIATED,
            governance_autonomy=GovernanceAutonomy.AUTONOMOUS,
        )
        assert org.parent_relationship == ParentRelationship.AFFILIATED
        assert org.governance_autonomy == GovernanceAutonomy.AUTONOMOUS


class TestSerialization:
    def test_roundtrip_preserves_values(self):
        org = OrganizationModel(
            organization_id="org-001",
            name="Test Org",
            parent_relationship=ParentRelationship.SYSTEM_MEMBER,
            unit_granularity=UnitGranularity.SERVICE_LINE,
        )
        dumped = org.model_dump()
        # use_enum_values=True -> enums serialize to their string values.
        assert dumped["parent_relationship"] == "system_member"
        assert dumped["unit_granularity"] == "service_line"
        restored = OrganizationModel.model_validate(dumped)
        assert restored == org

    def test_unknown_field_is_rejected(self):
        with pytest.raises(ValidationError):
            OrganizationModel(
                organization_id="org-001",
                name="Test Org",
                bogus_field="nope",
            )

    def test_invalid_enum_value_is_rejected(self):
        with pytest.raises(ValidationError):
            OrganizationModel(
                organization_id="org-001",
                name="Test Org",
                governance_autonomy="not_a_real_value",
            )
