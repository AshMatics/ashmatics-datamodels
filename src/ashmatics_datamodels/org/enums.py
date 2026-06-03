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
Organization governance-boundary enumerations (FORGE-aligned).

These three enums are the single source of truth for the organization
governance-boundary vocabulary. coreapp's Django ``Organization`` model imports
them (see JAC-12 / JAC-27 and ADR-002) instead of re-declaring its own copies —
that re-declaration was the per-repo drift ADR-002 exists to retire.

Binding to the ontology is asserted on the *model fields* that use these enums
(``x_ontology_scheme`` in ``organization.py``), not on the enums themselves, per
the ADR-002 annotation convention. The IRIs each enum corresponds to are recorded
here in prose so the intent is greppable; the CI guard
(``tests/org/test_ontology_binding.py``) checks every member resolves to a real
SKOS concept in the FORGE ConceptScheme.

Source ontology: ``ashmatics-ontology/forge-organizational-ontology.ttl`` (forge:),
which ``owl:imports`` ``ashmatics-unified-ontology.ttl`` (ash: / ashcai:).
"""

from enum import Enum


class ParentRelationship(str, Enum):
    """
    Types the *structure* edge (``Organization.parent``) — how an org relates to
    its parent. This is a **discriminator**, not a SKOS ConceptScheme: FORGE models
    each relationship as a distinct object property, and this enum selects which
    one the structure edge realizes. The governance edge is separate
    (see :class:`GovernanceAutonomy` and ``governed_by``).

    Per-value FORGE binding:

    - ``NONE``           — no structure edge; a standalone / root organization.
    - ``PROVIDER_BASED`` — ``forge:providerBasedTo``. Facility operates under the
      parent's CCN (42 CFR 413.65); **governance inherits** across this edge.
    - ``SYSTEM_MEMBER``  — ``forge:memberOf`` (inverse ``forge:hasMember``).
      Health-system membership / enterprise composition (TCS-4).
    - ``AFFILIATED``     — ``forge:ownedBy``. Corporate ownership / affiliation
      **only**; governance does NOT inherit (contrast ``providerBasedTo``).

    Because it spans three properties plus a "no edge" sentinel, this field carries
    no single ``x_ontology_scheme``/``x_ontology_property``. Formalizing the link
    (e.g. declaring ``forge:memberOf``/``forge:ownedBy`` as
    ``rdfs:subPropertyOf ash:part_of``) is an ontology-repo follow-on, not done here.
    """

    NONE = "none"
    PROVIDER_BASED = "provider_based"
    SYSTEM_MEMBER = "system_member"
    AFFILIATED = "affiliated"


class GovernanceAutonomy(str, Enum):
    """
    The decisive governance-boundary flag: whether an org holds its own AI
    governance authority or inherits one via ``governed_by``.

    Binds 1:1 to the ``forge:GovernanceAutonomy`` SKOS ConceptScheme
    (``forge:autonomy-autonomous`` / ``forge:autonomy-inherited``). Drives
    blueprint meshing (JAC-25): autonomous → full self-contained AIMS;
    inherited → unit-local artifacts that reference the governing org's policies.
    """

    AUTONOMOUS = "autonomous"
    INHERITED = "inherited"


class UnitGranularity(str, Enum):
    """
    Granularity of an organizational or clinical unit — the Axis-2 driving function
    for scope_profiles candidate-domain sizing (JAC-26): a narrow unit (section,
    lab) gets a tight process-domain set; a broad band (system, enterprise) gets a
    wider one. Granularity is an EXPLICIT tag, never inferred from nesting depth.

    Binds 1:1 to the ``forge:UnitGranularity`` SKOS ConceptScheme (FORGE v0.6.0);
    each member value matches a concept ``skos:notation``. The axis spans org-level
    bands (system, enterprise, practice) and clinical-unit bands (institute … lab),
    and subsumes coreapp's former ``BlueprintScopeType`` vocabulary into one scale.

    RECONCILED (JAC-27, 2026-06-02): FORGE was extended with the org-level bands
    (decision: those are real US health-system levels) rather than narrowing
    coreapp. This enum now matches coreapp's Django ``UnitGranularity`` value-for-
    value, so coreapp can single-source from here.
    """

    SYSTEM = "system"
    ENTERPRISE = "enterprise"
    INSTITUTE = "institute"
    SERVICE_LINE = "service_line"
    DEPARTMENT = "department"
    DIVISION = "division"
    SECTION = "section"
    PROGRAM = "program"
    LAB = "lab"
    PRACTICE = "practice"
