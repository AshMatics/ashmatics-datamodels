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

"""Tests for the ADR-057 site role contracts (ASHFORGE-370)."""

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.org import (
    ApprovedSiteRoleSet,
    SiteRole,
    SiteRoleAdjustment,
    SiteRoleHolder,
    SiteRoleHolderKind,
)


class TestSiteRoleGrouping:
    def test_a_role_covers_several_char_tokens(self):
        # ADR-057 D1: a site role groups several CHAR responsibilities.
        role = SiteRole(
            role_id="role-1",
            label="Value & Workflow Lead",
            covers=["health_economist", "workflow_analyst"],
        )
        assert role.covers == ["health_economist", "workflow_analyst"]

    def test_covers_requires_at_least_one_token(self):
        with pytest.raises(ValidationError):
            SiteRole(role_id="role-1", label="Empty Role", covers=[])

    def test_no_is_class_bound_flag_is_stored(self):
        # D3: coreapp stores no "is class bound" flag on a covered token —
        # duplicating that answer would drift. Pin the field set so one
        # cannot silently reappear.
        assert "covers" in SiteRole.model_fields
        for name in SiteRole.model_fields:
            assert "class_bound" not in name
            assert "is_slot" not in name


class TestSiteRoleHolder:
    def test_person_holder(self):
        holder = SiteRoleHolder(
            kind=SiteRoleHolderKind.PERSON, holder_id="user-42", display_name="Dana"
        )
        assert holder.kind == "person"

    def test_agent_holder(self):
        holder = SiteRoleHolder(kind=SiteRoleHolderKind.AGENT, holder_id="agent-hazard-triage")
        assert holder.kind == "agent"

    def test_holder_id_required(self):
        with pytest.raises(ValidationError):
            SiteRoleHolder(kind=SiteRoleHolderKind.PERSON, holder_id="")


class TestProposalProvenance:
    def test_unaccepted_proposal_has_no_holder(self):
        # D7: a proposal is never applied unaccepted. A role with no
        # accepted_at legitimately holds no one.
        role = SiteRole(
            role_id="role-2",
            label="Safety Lead",
            covers=["safety_analyst"],
            agent_rank=1,
        )
        assert role.holder is None
        assert role.is_accepted is False

    def test_accepted_proposal_is_accepted(self):
        role = SiteRole(
            role_id="role-2",
            label="Safety Lead",
            covers=["safety_analyst"],
            agent_rank=1,
            accepted_at="2026-09-21T00:00:00Z",
            accepted_by="user-1",
        )
        assert role.is_accepted is True

    def test_rejected_proposal_is_not_accepted_even_with_a_timestamp(self):
        # Reintroduce the bug: if is_accepted only checked accepted_at, a row
        # that was accepted and later rejected would still read as accepted.
        role = SiteRole(
            role_id="role-2",
            label="Safety Lead",
            covers=["safety_analyst"],
            accepted_at="2026-09-21T00:00:00Z",
            accepted_by="user-1",
            rejected_at="2026-09-22T00:00:00Z",
        )
        assert role.is_accepted is False


class TestSiteRoleAdjustment:
    def test_rationale_is_mandatory(self):
        with pytest.raises(ValidationError):
            SiteRoleAdjustment(action="grouped", rationale="")

    def test_adjustment_records_who_and_why(self):
        adj = SiteRoleAdjustment(
            action="grouped",
            covers=["health_economist", "workflow_analyst"],
            rationale="One analyst does both jobs at our size.",
            adjusted_by="user-1",
        )
        assert adj.action == "grouped"


class TestApprovedSiteRoleSet:
    def test_resolved_list_and_adjustment_provenance(self):
        role = SiteRole(
            role_id="role-1",
            label="Value & Workflow Lead",
            covers=["health_economist", "workflow_analyst"],
            holder=SiteRoleHolder(kind=SiteRoleHolderKind.PERSON, holder_id="user-9"),
        )
        adjustment = SiteRoleAdjustment(
            action="grouped",
            covers=["health_economist", "workflow_analyst"],
            rationale="One analyst does both jobs at our size.",
        )
        role_set = ApprovedSiteRoleSet(
            organization_id="org-1",
            roles=[role],
            adjustments=[adjustment],
        )
        assert role_set.roles[0].covers == ["health_economist", "workflow_analyst"]
        assert role_set.adjustments[0].rationale

    def test_organization_id_required(self):
        with pytest.raises(ValidationError):
            ApprovedSiteRoleSet(organization_id="")

    def test_starts_empty(self):
        # D5: the list builds itself from the plays a site turns on, and
        # starts empty.
        role_set = ApprovedSiteRoleSet(organization_id="org-1")
        assert role_set.roles == []
        assert role_set.adjustments == []


class TestModelIsNotOntologyAnchored:
    def test_no_x_ontology_annotations(self):
        # Mirrors methods.method_sets' posture: deliberately not anchored yet.
        for model in (SiteRole, ApprovedSiteRoleSet, SiteRoleAdjustment, SiteRoleHolder):
            extra = model.model_config.get("json_schema_extra") or {}
            assert "x_ontology_class" not in extra
