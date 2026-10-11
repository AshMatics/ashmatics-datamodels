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
CHAR method-definition contracts (aigov-framework ADR-011 §5).

``MethodDefinition`` and its parts model the shapes in the aigov-framework
``method_registry.yaml`` field-for-field: the YAML is the spec, these
contracts make it portable and guarded. The registry stores exemplar
defaults ONLY; per-client rules live client-side (coreapp MethodRoute,
ADR-031).

ADR-002 binding convention:

- ``x_ontology_class``    on ``model_config.json_schema_extra`` — the
  ontology class the model realizes.
- ``x_ontology_property`` on a ``Field`` — the ontology object property the
  field stands for (here: the ``ashcai:methodAppliesTo`` subproperties).
- ``x_ontology_scheme``   on an enum-backed ``Field`` — the SKOS
  ConceptScheme whose concepts are the field's legal values.

A ``MethodDefinition``'s ``method_id`` is the ``skos:notation`` of exactly
one concept in ``ashcai:GovernanceMethodScheme`` (ontology ADR-006); the
CI guard in ``tests/methods/test_ontology_binding.py`` enforces the scheme
bindings against the Turtle source.
"""

from datetime import date
from typing import Annotated

from pydantic import (
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.common.enums import ActionAuthority

from .enums import (
    AIParadigm,
    EvidenceType,
    FairnessFactor,
    ForbiddenDecision,
    InputModality,
    MethodFamily,
    MethodPhase,
    ModelClass,
    OutputForm,
    RobustnessFactor,
)

# ID grammars shared with the aigov-framework validators. Kept as module
# constants so consumers (e.g. validate_method_registry.py) import one truth.
METHOD_ID_PATTERN = r"^mth://[a-z0-9_]+(\.[a-z0-9_]+)+$"
METHOD_SET_ID_PATTERN = r"^mset://[a-z0-9_]+(\.[a-z0-9_]+)+$"
JUNCTION_REF_PATTERN = r"^SOP-[A-Z]+-\d{2}\.S[\d.]+$"
POLICY_TOKEN_PATTERN = r"^\{\{[A-Za-z0-9_.]+\}\}$"
#updated tool token pattern post the changes of how we tag tools, 2026-09-06
TOOL_TOKEN_PATTERN = r"^\{\{tool\.[A-Za-z0-9_]+\}\}$"

# Annotated string types so list items validate per element.
MethodId = Annotated[str, StringConstraints(pattern=METHOD_ID_PATTERN)]
MethodSetId = Annotated[str, StringConstraints(pattern=METHOD_SET_ID_PATTERN)]
JunctionRef = Annotated[str, StringConstraints(pattern=JUNCTION_REF_PATTERN)]
ToolToken = Annotated[str, StringConstraints(pattern=TOOL_TOKEN_PATTERN)]
PolicyToken = Annotated[str, StringConstraints(pattern=POLICY_TOKEN_PATTERN)]


class EvidenceRef(AshMaticsBaseModel):
    """One entry in a method's mandatory evidence basis (ADR-011)."""

    type: EvidenceType = Field(
        ..., description="Kind of reference (doi, arxiv, ref, guidance, "
        "standard, regulation)."
    )
    ref: str = Field(
        ..., min_length=1,
        description="The reference itself: DOI, arXiv id, citation string, "
        "or standard/regulation designation.",
    )
    note: str | None = Field(
        None, description="What this reference establishes for the method."
    )


class DefaultRule(AshMaticsBaseModel):
    """
    An exemplar default-selection rule: when ``condition`` holds for an AI
    system, this method is a rank-ordered default candidate. Conditions use
    the CLF expression grammar with ``{{system.*}}`` tokens, or, for a method
    chosen per hazard record, ``{{record.*}}`` tokens; every such token must
    be registered in the CLF system or record scope (enforced by the
    aigov-framework registry validator, which has the CLF block in hand).
    """

    condition: str = Field(
        ..., min_length=1,
        description="CLF condition expression, e.g. "
        "\"{{system.riskTier}} == 'high'\".",
    )
    rank: int = Field(
        ..., ge=1,
        description="1 = strongest default among rules whose conditions hold.",
    )


class MethodReview(AshMaticsBaseModel):
    """Registry review-cycle bookkeeping for one method."""

    last_reviewed: date = Field(
        ..., description="Date of the last content review of this entry."
    )


class DepthApplicability(AshMaticsBaseModel):
    """
    Where a method is MANDATORY, as against preferred (aigov-framework
    ``method_registry.yaml``, header of the hazard analysis family;
    ASHFORGE-828). ``default_for`` is preference, a rank among candidates;
    this is the rule of ``harm_model.yaml``'s analysis depth in a form a gate
    can read::

        depth_applicability:
          mandatory_at_harm_levels: [4, 5]
          harm_model_tier: full_safety_analysis

    THE READING IS ANY ONE OF. For a hazard record at harm level L, take the
    methods of the family whose ``mandatory_at_harm_levels`` contains L; if
    there are any, the method chosen for the record must be one of them. The
    set is computed over the registry's family, not a site's narrowed set. A
    method mandatory nowhere carries an empty list.

    What this contract checks is what the record alone shows: each level is
    1 to 5, and a method that is mandatory somewhere names the tier that sets
    the rule. That the levels are exactly the tier's levels in
    ``harm_model.yaml`` is a cross-file check and stays in the framework's
    ``validate_method_registry.py``; this package does not carry the harm
    model (``risk.AnalysisDepth`` names the tiers, but ``methods`` cannot
    import ``risk``, which imports ``methods``).
    """

    mandatory_at_harm_levels: list[Annotated[int, Field(ge=1, le=5)]] = Field(
        default_factory=list,
        description="Harm levels (1-5, the harm model's scale) of a hazard "
        "record at which the method is mandatory. Empty where it is "
        "mandatory nowhere.",
    )
    harm_model_tier: str | None = Field(
        None, min_length=1,
        description="The harm_model.yaml analysis_depth tier that sets the "
        "rule, e.g. full_safety_analysis. Required when "
        "mandatory_at_harm_levels is not empty.",
    )

    @model_validator(mode="after")
    def _mandatory_levels_name_their_tier(self) -> "DepthApplicability":
        if self.mandatory_at_harm_levels and not self.harm_model_tier:
            raise ValueError(
                "harm_model_tier is required when mandatory_at_harm_levels "
                "is not empty: a level is mandatory because of a tier"
            )
        return self


class ApplicabilityProfile(AshMaticsBaseModel):
    """
    SKOS-bound applicability axes: which systems a method is applicable to,
    expressed exclusively as ash facet-scheme concepts (zero free strings,
    ADR-011's core success criterion). Each axis field realizes one
    ``ashcai:methodAppliesTo`` subproperty. Non-SKOS numeric/boolean
    prerequisites ride along as plain typed fields.
    """

    ai_paradigm: list[AIParadigm] | None = Field(
        None,
        description="AI paradigms the method applies to.",
        json_schema_extra={
            "x_ontology_scheme": "ash:AIParadigmScheme",
            "x_ontology_property": "ashcai:appliesToParadigm",
        },
    )
    output_form: list[OutputForm] | None = Field(
        None,
        description="Output forms the method applies to.",
        json_schema_extra={
            "x_ontology_scheme": "ash:OutputFormScheme",
            "x_ontology_property": "ashcai:appliesToOutputForm",
        },
    )
    input_modality: list[InputModality] | None = Field(
        None,
        description="Input modalities the method applies to.",
        json_schema_extra={
            "x_ontology_scheme": "ash:InputModalityScheme",
            "x_ontology_property": "ashcai:appliesToInputModality",
        },
    )
    fairness_factors: list[FairnessFactor] | None = Field(
        None,
        description="Fairness stratification factors the method addresses.",
        json_schema_extra={
            "x_ontology_scheme": "ash:FairnessFactorScheme",
            "x_ontology_property": "ashcai:appliesToFairnessFactor",
        },
    )
    robustness_factors: list[RobustnessFactor] | None = Field(
        None,
        description="Robustness factors the method addresses. No registry "
        "v0.1.0 method binds this axis; contracted ahead of the "
        "imaging-robustness method wave.",
        json_schema_extra={
            "x_ontology_scheme": "ash:RobustnessFactorScheme",
            "x_ontology_property": "ashcai:appliesToRobustnessFactor",
        },
    )
    model_class: list[ModelClass] | None = Field(
        None,
        description="Model classes the method is amenable to (ontology "
        "ADR-006), e.g. TreeSHAP exactness for tree ensembles. No registry "
        "v0.1.0 method binds this axis yet.",
        json_schema_extra={
            "x_ontology_scheme": "ash:ModelClassScheme",
            "x_ontology_property": "ashcai:appliesToModelClass",
        },
    )

    # Non-SKOS prerequisites (plain typed fields, not scheme-bound).
    action_authority: list[ActionAuthority] | None = Field(
        None,
        description="Action authority levels the method applies to — what "
        "the system may do without a human in the loop.",
        json_schema_extra={
            "x_ontology_scheme": "ash:ActionAuthorityScheme",
            "x_ontology_property": "ashcai:appliesToActionAuthority",
        },
    )
    min_subgroup_n: int | None = Field(
        None, ge=1,
        description="Minimum per-stratum sample size for the method's "
        "statistics to be meaningful.",
    )
    requires_retraining_access: bool | None = Field(
        None,
        description="Whether the method requires retraining access to the "
        "model (drives bias-mitigation family selection via "
        "{{system.retrainingAccess}}).",
    )


class MethodDefinition(AshMaticsBaseModel):
    """
    One exemplar governance method: an analytical technique executed within
    an SOP step (the CHAR vocabulary spine's method stratum). Anchored 1:1
    to an ``ashcai:GovernanceMethodScheme`` concept whose ``skos:notation``
    equals ``method_id``.
    """

    model_config = ConfigDict(
        json_schema_extra={"x_ontology_class": "ashcai:GovernanceMethodScheme"}
    )

    method_id: MethodId = Field(
        ...,
        description="Registry ID and ontology notation, mth://family.name form.",
    )
    label: str = Field(
        ..., min_length=1,
        description="Human-readable name (the concept's skos:prefLabel).",
    )
    family: MethodFamily = Field(
        ...,
        description="Method family; the concept's skos:broader parent.",
        json_schema_extra={
            "x_ontology_scheme": "ashcai:GovernanceMethodScheme",
        },
    )
    description: str = Field(
        ..., min_length=1,
        description="What the method does and when it is (in)appropriate "
        "(the concept's skos:definition).",
    )
    junction_refs: list[JunctionRef] = Field(
        ..., min_length=1,
        description="SOP-step junction anchors (SOP-XX-NN.Sn) from the "
        "authoritative junction inventory.",
    )
    executable_by: list[ToolToken] = Field(
        default_factory=list,
        description="tool capability tokens that execute "
        "this method; empty when execution is manual/external. These can be in FORGE, external tools, or 3P.Tools execute "
        "methods, they are not methods.",
    )
    phase: MethodPhase = Field(
        ..., description="Lifecycle phase(s) the method serves."
    )
    applicability: ApplicabilityProfile = Field(
        ..., description="SKOS-bound applicability axes plus non-SKOS "
        "prerequisites."
    )
    evidence_basis: list[EvidenceRef] = Field(
        ..., min_length=1,
        description="Mandatory literature/guidance basis (ADR-011).",
    )
    default_for: list[DefaultRule] = Field(
        default_factory=list,
        description="Exemplar default-selection rules; may be empty for "
        "methods that are never defaults (e.g. demographic parity).",
    )
    depth_applicability: DepthApplicability | None = Field(
        None,
        description="Where the method is mandatory, as against preferred "
        "(default_for). Absent on every method that is not part of a family "
        "with a depth rule. The hazard_analysis family carries it on all six "
        "methods, with an empty list where a method is mandatory nowhere.",
    )
    forbidden_decisions: list[ForbiddenDecision] | None = Field(
        None,
        description="What applying the method never decides, whoever or "
        "whatever applies it. A closed list; no repeats. Absent where the "
        "method has no such statement. The hazard_analysis family carries "
        "the same four on all six methods.",
    )
    review: MethodReview = Field(
        ..., description="Review-cycle bookkeeping."
    )

    @field_validator("forbidden_decisions")
    @classmethod
    def _forbidden_decisions_are_a_set(
        cls, v: list[ForbiddenDecision] | None
    ) -> list[ForbiddenDecision] | None:
        if v is not None and len(set(v)) != len(v):
            raise ValueError("forbidden_decisions must not repeat a decision")
        return v
