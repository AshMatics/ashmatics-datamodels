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
Method-set contracts (aigov-framework ADR-011 §4).

A ``MethodSet`` is one org-approvable set serving multiple SOP junction
sites with phase-appropriate member variants — the mechanism that collapsed
the five historically duplicated bias/fairness junction sites onto
``mset://fairness.core``. ``ApprovedMethodSet`` is the client-resolved
variant a Blueprint emits.

Set/junction concepts are deliberately NOT ontology-anchored yet: minting
them is deferred until the terminology service defines sub-document anchor
references (uplift plan Phase 4 item 19; ontology handoff work item 4), so
these models carry no ``x_ontology_*`` annotations.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .enums import DeliveryMode, MethodPhase
from .methods import JunctionRef, MethodId, MethodSetId, PolicyToken

# members/resolved_members keys: only the two concrete phases. A set never
# keys members by "both" — a method serving both phases appears under each.
MemberPhase = Literal["validation", "operational"]


class JunctionBinding(AshMaticsBaseModel):
    """One junction site a method set serves, with its phase variant."""

    ref: JunctionRef = Field(
        ..., description="SOP-step junction anchor (SOP-XX-NN.Sn)."
    )
    phase: MethodPhase = Field(
        ..., description="Which phase variant of the set this site receives."
    )
    note: str | None = Field(
        None, description="Site role, e.g. 'primary definition site'."
    )


class MethodSet(AshMaticsBaseModel):
    """
    An exemplar shared method set: one approval decision serving multiple
    junction sites so validation findings and production monitoring
    reference identical method definitions (no forked lists).
    """

    set_id: MethodSetId = Field(
        ..., description="Registry set ID, mset://area.name form."
    )
    label: str = Field(..., min_length=1, description="Human-readable name.")
    description: str = Field(
        ..., min_length=1,
        description="What the set covers and how phase variants relate.",
    )
    serves_junctions: list[JunctionBinding] = Field(
        ..., min_length=1,
        description="Junction sites resolving against this set.",
    )
    members: dict[MemberPhase, list[MethodId]] = Field(
        ...,
        description="Member method IDs keyed by phase; a method serving "
        "both phases is listed under each.",
    )
    token: PolicyToken = Field(
        ...,
        description="The {{token}} SOP junctions render this set through.",
    )
    token_aliases: list[PolicyToken] | None = Field(
        None,
        description="Legacy/alternate tokens resolving to the same set "
        "(e.g. the EF statistical-methods alias onto the SA framework set).",
    )


class MethodSetAdjustment(AshMaticsBaseModel):
    """
    Provenance of one client deviation from the exemplar set. Rationale is
    mandatory: overrides without rationale are exactly what the CLF
    ``require_method_rationale_on_override`` action exists to prevent.
    """

    action: Literal["added", "removed", "reranked"] = Field(
        ..., description="What changed relative to the exemplar set."
    )
    method_id: MethodId = Field(..., description="The method affected.")
    phase: MethodPhase = Field(
        ..., description="Which phase variant the adjustment applies to."
    )
    rationale: str = Field(
        ..., min_length=1,
        description="Why the client deviated from the exemplar (mandatory).",
    )
    adjusted_by: str | None = Field(
        None, description="User or role that made the adjustment."
    )
    adjusted_at: datetime | None = Field(
        None, description="When the adjustment was made."
    )


class ApprovedMethodSet(MethodSet):
    """
    The client-resolved variant of a MethodSet (Blueprint output): the
    exemplar set plus org context, the resolved member list after client
    adjustments, delivery mode, and adjustment provenance. Inherited
    ``members`` holds the exemplar baseline; ``resolved_members`` is what
    the client actually approved.
    """

    organization_id: str = Field(
        ..., min_length=1,
        description="The approving org (org module organization_id).",
    )
    resolved_members: dict[MemberPhase, list[MethodId]] = Field(
        ...,
        description="Post-adjustment member list the org approved, keyed "
        "by phase.",
    )
    delivery_mode: DeliveryMode = Field(
        ...,
        description="Blueprint delivery mode "
        "(Generate / Augment / Align / Reference).",
    )
    adjustments: list[MethodSetAdjustment] = Field(
        default_factory=list,
        description="Provenance of every deviation from the exemplar set; "
        "empty means adopted as-is.",
    )
    approved_by: str | None = Field(
        None, description="Governance authority that approved the set."
    )
    approved_at: datetime | None = Field(
        None, description="When the set was approved."
    )
