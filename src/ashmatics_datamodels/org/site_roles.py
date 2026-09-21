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
Site role contracts (ADR-057, ASHFORGE-370 / ASHFORGE-716 / ASHFORGE-717).

A site role is a hospital's own named role, grouping one or more CHAR
stakeholder-registry role or slot tokens (ADR-057 D1). CHAR names
responsibilities; a hospital names positions, and one person holds many
responsibilities. `ApprovedSiteRoleSet` is modeled on `methods.ApprovedMethodSet`
per ADR-057 D8: the CHAR registry is the exemplar, the site's roles are the
resolved list, and every deviation from a straight one-token-per-role mapping
carries who made it and why.

Deliberately NOT ontology-anchored yet, the same posture `methods.method_sets`
takes for sets and junctions: a site role is customer org structure and
`forge:` is its eventual home (ADR-057 context), but minting that vocabulary is
deferred until the shape has settled against real use (ADR-048 §8). These
models carry no `x_ontology_*` annotations.

CLASS RESOLUTION IS NOT MODELED HERE (ADR-057 D3). A token in `covers` is
either a plain CHAR role or a slot that resolves to one of two concrete roles
by the subject system's class. That resolution is coreapp's job at read time,
against its CHAR mirror, and this package stores no "is class bound" flag —
duplicating that answer would drift. `covers` holds tokens exactly as CHAR
spells them (and exactly as WS-25 writes them onto a lane), undifferentiated.

HOLDING GRANTS NOTHING (ADR-057 D4). `SiteRoleHolder` records who holds a role.
It authorizes nothing and is not an ADR-045 authorization group.

A PROPOSAL IS NEVER APPLIED UNACCEPTED (ADR-057 D7). `SiteRole` carries the
same proposal-provenance shape as `core.models.aims_artifacts.MethodCandidate`
(`agent_rank`, `accepted_at`, `accepted_by`, `rejected_at`,
`customization_note`) so an assistant-proposed grouping can be stored before a
GovAdmin accepts it. `holder` is legitimately `None` on an unaccepted proposal.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel


class SiteRoleHolderKind(str, Enum):
    """Which kind of actor `SiteRoleHolder.holder_id` names (ADR-057 D4)."""

    PERSON = "person"
    AGENT = "agent"


class SiteRoleHolder(AshMaticsBaseModel):
    """
    Who currently holds a site role (ADR-057 D4). Records holding only — grants
    nothing, executes nothing and authorizes nothing. This is the first
    non-human actor this package models: `kind` distinguishes a platform user
    from a named agent, and `holder_id` is that actor's id under the matching
    system (coreapp user id, or agent reference id).
    """

    kind: SiteRoleHolderKind = Field(
        ..., description="Whether the holder is a platform user or an agent."
    )
    holder_id: str = Field(
        ..., min_length=1,
        description="Platform user id or agent reference id, by kind.",
    )
    display_name: str | None = Field(
        None,
        description="The holder's display name at binding time, so a record "
        "still reads after a rename.",
    )


class SiteRoleAdjustment(AshMaticsBaseModel):
    """
    Provenance of one deviation from a straight one-CHAR-token-per-role
    mapping (ADR-057 D8). Rationale is mandatory, the same discipline
    `MethodSetAdjustment` holds for a method-set override: a grouping made
    without a stated reason is exactly what this field exists to prevent.
    """

    action: Literal["grouped", "renamed", "holder_changed", "removed"] = Field(
        ..., description="What changed relative to a straight token mapping."
    )
    covers: list[str] | None = Field(
        None,
        description="CHAR tokens affected, when the action changes what the "
        "role covers (e.g. 'grouped').",
    )
    rationale: str = Field(
        ..., min_length=1,
        description="Why the site deviated from the exemplar (mandatory).",
    )
    adjusted_by: str | None = Field(
        None, description="User or role that made the adjustment."
    )
    adjusted_at: datetime | None = Field(
        None, description="When the adjustment was made."
    )


class SiteRole(AshMaticsBaseModel):
    """
    One organization-named role that groups one or more CHAR role/slot tokens
    (ADR-057 D1). The list builds itself from the plays a site turns on and
    starts empty (D5): a site with one health economist names a role covering
    exactly one token; a site that folds the economist and the workflow
    analyst together names one role covering two. Same structure, different
    count.
    """

    role_id: str = Field(..., min_length=1, description="Stable id.")
    label: str = Field(
        ..., min_length=1, description="The site's own name for the role."
    )
    description: str = Field(
        "", description="What the role covers, in the site's own words."
    )
    covers: list[str] = Field(
        ..., min_length=1,
        description="CHAR role/slot tokens this role groups (ADR-057 D1, "
        "D3). A plain role or a slot, undifferentiated — the registry "
        "answers which at read time.",
    )
    holder: SiteRoleHolder | None = Field(
        None,
        description="Who holds the role today. None on a role that has not "
        "yet been accepted (D7), or on one deliberately left unassigned.",
    )

    # Proposal provenance (ADR-057 D7), the `MethodCandidate` pattern:
    # `ApprovedMethodSet`'s sibling for an assistant-proposed grouping a
    # person has not yet accepted. A proposal is never applied unaccepted.
    agent_rank: int | None = Field(
        None,
        description="Rank among proposed groupings for the same site, when "
        "agent-proposed. None for a role a person authored directly.",
    )
    accepted_at: datetime | None = Field(
        None, description="When a person accepted this role (or its most "
        "recent grouping)."
    )
    accepted_by: str | None = Field(
        None, description="Who accepted it."
    )
    rejected_at: datetime | None = Field(
        None, description="When a person rejected the proposed grouping."
    )
    customization_note: str = Field(
        "",
        description="Free-form note when a person customized the proposed "
        "grouping before accepting it.",
    )

    @property
    def is_accepted(self) -> bool:
        """A proposal is never applied unaccepted (ADR-057 D7)."""
        return self.accepted_at is not None and self.rejected_at is None


class ApprovedSiteRoleSet(AshMaticsBaseModel):
    """
    The org-resolved list of site roles (ADR-057 D8), `ApprovedMethodSet`'s
    sibling: the CHAR registry is the exemplar (referenced only by the tokens
    in each role's `covers`, never re-minted here), `roles` is the resolved
    list the site actually holds, and `adjustments` is provenance of every
    deviation from a straight token mapping.

    A durable organization record (ADR-057 consequences, ADR-056's test):
    another play, or a later run of the same play, reads a site's roles, so
    this is organization state, never a run answer.
    """

    organization_id: str = Field(
        ..., min_length=1,
        description="The organization this role set belongs to.",
    )
    roles: list[SiteRole] = Field(
        default_factory=list,
        description="The site's roles, accepted and proposed alike; "
        "`SiteRole.is_accepted` distinguishes them.",
    )
    adjustments: list[SiteRoleAdjustment] = Field(
        default_factory=list,
        description="Provenance of every deviation from a straight token "
        "mapping; empty means every role covers exactly one token.",
    )
    approved_by: str | None = Field(
        None, description="Governance authority that approved this role set."
    )
    approved_at: datetime | None = Field(
        None, description="When the role set was approved."
    )
