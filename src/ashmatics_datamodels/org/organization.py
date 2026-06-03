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
Canonical organization-instance shape (FORGE-annotated).

This is the shared, on-the-wire shape of a customer organization's governance
boundary — the WHO/WHERE an AI Management System and its policies apply to. It is
the contract layer of ADR-002: coreapp's Django ``Organization`` is the
operational system of record and conforms to this shape; the MongoDB FORGE
projection (JAC-23) serializes it; the Stage A wizard and agentic SOP inference
read it.

ADR-002 binding convention (the "prototype" this story proves):

- ``x_ontology_class``    on ``model_config.json_schema_extra`` — the ontology
  Class IRI this model realizes.
- ``x_ontology_property`` on a reference/value ``Field`` — the ontology object/
  datatype property IRI the field stands for.
- ``x_ontology_scheme``   on an enum-backed ``Field`` — the SKOS ConceptScheme IRI
  whose concepts are the field's legal values.

Keys are flat (ADR-002 open-question #2, resolved). The CI guard
(``tests/org/test_ontology_binding.py``) parses the FORGE + unified ``.ttl`` and
fails on any annotated IRI that does not resolve — drift becomes a failed test,
not a silent production bug.

SCOPE (v1 prototype): one flat ``OrganizationModel`` mirrors coreapp's reality,
where org / facility / clinical-unit are not yet separate entities (ADR-020 §12.8
decision 1: granularity *tag* only, no ``ClinicalUnit`` entity yet). FORGE splits
some of these properties across ``forge:Organization`` / ``forge:Facility`` /
``forge:ClinicalUnit``; where a field's FORGE domain is Facility or ClinicalUnit
the divergence is noted on the field. Modeling those as distinct nested entities is
a follow-on, not this prototype.
"""

from pydantic import ConfigDict, Field

from ashmatics_datamodels.common.base import TimestampedModel

from .enums import GovernanceAutonomy, ParentRelationship, UnitGranularity


class OrganizationModel(TimestampedModel):
    """
    A customer organization's governance-boundary instance — realizes
    ``forge:Organization`` (subclass of ``prov:Agent``).

    Holds the two edges that ADR-020 v0.3 §12 separates:

    - the **structure** edge (``parent_id`` + ``parent_relationship``), and
    - the **governance** edge (``governed_by_id`` + ``governance_autonomy``),

    which genuinely diverge: an affiliated practice is *owned by* a parent yet
    *governed by* itself; a provider-based facility is a *facility of* a hospital
    and *governed by* that hospital.
    """

    model_config = ConfigDict(
        json_schema_extra={"x_ontology_class": "forge:Organization"}
    )

    # --- identity ---------------------------------------------------------
    organization_id: str = Field(
        ...,
        description="Stable instance identifier (the node key in the FORGE "
        "projection). Application-managed; not an ontology property.",
    )
    name: str = Field(..., description="Human-readable organization name.")

    organization_type: str | None = Field(
        None,
        description="Classifies the org by an ash HealthCareRelatedOrganization "
        "concept (range ash:SemanticType_T093). Value is an ash concept "
        "id/IRI, e.g. a SiteOfCare or practice-type concept.",
        json_schema_extra={"x_ontology_property": "forge:organizationType"},
    )
    segment: str | None = Field(
        None,
        description="Internal GTM market segment tag (TCS-1..5) — "
        "forge:hasSegment is an attribute, never customer-facing org structure. "
        "Value is a forge:MarketSegment concept notation (e.g. 'TCS_3').",
        json_schema_extra={"x_ontology_property": "forge:hasSegment"},
    )

    # --- structure edge ---------------------------------------------------
    parent_id: str | None = Field(
        None,
        description="organization_id of the parent on the STRUCTURE edge. Which "
        "FORGE property this realizes is selected by parent_relationship "
        "(providerBasedTo / memberOf / ownedBy); no single x_ontology_property "
        "applies, so the binding lives in ParentRelationship's docs.",
    )
    parent_relationship: ParentRelationship = Field(
        ParentRelationship.NONE,
        description="Discriminator typing the structure edge. See "
        "ParentRelationship for the per-value FORGE property mapping.",
    )

    # --- governance edge --------------------------------------------------
    governed_by_id: str | None = Field(
        None,
        description="organization_id of the org whose AI governance authority "
        "applies here (FORGE: forge:governedBy). For inherited orgs without an "
        "explicit choice, onboarding defaults this to parent_id (a service-layer "
        "fallback, JAC-22 — not a model default).",
        json_schema_extra={"x_ontology_property": "forge:governedBy"},
    )
    governance_autonomy: GovernanceAutonomy = Field(
        GovernanceAutonomy.AUTONOMOUS,
        description="Whether this org holds its own AI governance authority or "
        "inherits one. Decisive flag for blueprint meshing.",
        json_schema_extra={"x_ontology_scheme": "forge:GovernanceAutonomy"},
    )

    # --- granularity & specialty (FORGE domain: ClinicalUnit; flattened here) -
    unit_granularity: UnitGranularity | None = Field(
        None,
        description="Granularity of this org/clinical unit; Axis-2 scope driver "
        "(JAC-26). FORGE domain is forge:ClinicalUnit; carried on the org here "
        "until a ClinicalUnit entity exists.",
        json_schema_extra={"x_ontology_scheme": "forge:UnitGranularity"},
    )
    specialty: str | None = Field(
        None,
        description="Links a clinical unit to an ash ClinicalSpecialty concept "
        "(range ash:SemanticType_T9002). FORGE domain is forge:ClinicalUnit.",
        json_schema_extra={"x_ontology_property": "forge:specialty"},
    )

    # --- CMS / provider-based identifiers ---------------------------------
    shares_ccn_with_parent: bool = Field(
        False,
        description="True for provider-based facilities operating under the "
        "parent's CCN (42 CFR 413.65). FORGE domain is forge:Facility.",
        json_schema_extra={"x_ontology_property": "forge:sharesCCNwithParent"},
    )
    cms_ccn: str | None = Field(
        None,
        description="CMS Certification Number.",
        json_schema_extra={"x_ontology_property": "forge:cmsCCN"},
    )
    npi: str | None = Field(
        None,
        description="National Provider Identifier (NPPES Type-1 or Type-2).",
        json_schema_extra={"x_ontology_property": "forge:npi"},
    )
