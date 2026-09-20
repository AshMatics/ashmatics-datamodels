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
CLF v0.6.0 rule-grammar extension types (aigov-framework ADR-011 §3).

The conditional_logic_framework block of the aigov-framework
process-domain-registry.json is the source shape; these types make the
v0.6.0 extensions (system condition scope, method_control actions,
evaluation_time) portable so coreapp's MethodRoute work (ADR-031) and the
framework share one rule grammar instead of drifting copies.

The enums (``ConditionScope``, ``EvaluationTime``, ``MethodControlAction``)
live in ``enums.py``; this module carries the structured registry-entry
shape for system-scope attributes.
"""

from typing import Literal

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel

CURIE_PATTERN = r"^(ash|ashcai|forge):[A-Za-z][A-Za-z0-9]*$"


class SystemAttribute(AshMaticsBaseModel):
    """
    One registered ``{{system.*}}`` condition attribute: a per-AI-system
    value resolved against the client's AI inventory and risk register at
    evaluation time. Only registered attributes may appear in condition
    expressions (the aigov-framework registry validator enforces this).

    Systems without ontology classification resolve to the non-conditional
    approved method list, never an error (ADR-011 degraded mode).
    """

    name: str = Field(
        ..., pattern=r"^system\.[a-z][A-Za-z0-9]*$",
        description="Token name as used in conditions, e.g. system.riskTier.",
    )
    type: Literal["string", "number", "integer", "boolean", "array", "object"] = Field(
        ..., description="CLF value type of the resolved attribute. "
        "system.harmLevel is the first integer attribute (ADR-031 D9)."
    )
    source: Literal["ai_inventory", "risk_register"] | None = Field(
        None,
        description="Operational store the value resolves from once the AI "
        "system is registered. Optional when skos_scheme alone defines the "
        "value space (classification attributes resolve from the inventory's "
        "ontology tagging).",
    )
    pre_registration_source: Literal["triage_record", "sourcing_decision_record"] | None = Field(
        None,
        description="Where the value resolves from BEFORE the AI system is "
        "registered. Intake screens on a handful of these attributes while "
        "there is no inventory entry to read yet: the request has been "
        "triaged but registration does not commit until a fast-track "
        "approval or a decision to proceed (ADR-033 D4). Absent means the "
        "attribute simply does not resolve before registration, which is "
        "correct for anything intake has no basis to answer. "
        "``triage_record`` is the Triage Record screens. "
        "``sourcing_decision_record`` is the Sourcing Decision Record "
        "(WP-SA-01), which says what is built here and what is bought before "
        "any system exists; ``system.solutionShape`` is derived from it.",
    )
    skos_scheme: str | None = Field(
        None, pattern=CURIE_PATTERN,
        description="SKOS ConceptScheme CURIE constraining legal values "
        "(e.g. ash:AIParadigmScheme); None for plain-typed attributes.",
    )
    allowed_values: list[str | int] | None = Field(
        None,
        description="Closed value set carried inline so validators need no "
        "ontology runtime; kept in step with skos_scheme where both are set. "
        "For an array attribute, the legal members.",
    )
    deprecated: bool = False
    superseded_by: str | None = Field(
        None, pattern=r"^system\.[a-z][A-Za-z0-9]*$",
        description="The attribute that replaces a deprecated one.",
    )
    note: str | None = Field(
        None, description="Registry annotation, e.g. what the attribute drives."
    )

    @model_validator(mode="after")
    def _superseded_only_when_deprecated(self) -> "SystemAttribute":
        if self.superseded_by and not self.deprecated:
            raise ValueError("superseded_by is set on an attribute not marked deprecated")
        return self

    @model_validator(mode="after")
    def _pre_registration_needs_a_registered_source(self) -> "SystemAttribute":
        """
        An attribute that resolves before registration must also resolve
        after it. ``pre_registration_source`` says where the value comes
        from in the gap; it never replaces the operational store, because
        the system does get registered and the value has to keep resolving.
        A pre-registration source on an attribute that resolves nowhere
        afterwards describes something that works at intake and then stops,
        which is not a thing the framework can evaluate. ``skos_scheme``
        counts: a classification attribute resolves from the inventory's
        ontology tagging without naming a store, which is how
        ``system.aiParadigm`` is registered.
        """
        if self.pre_registration_source and not (self.source or self.skos_scheme):
            raise ValueError(
                "pre_registration_source is set on an attribute that resolves nowhere "
                "after registration: it says where the value resolves before "
                "registration, not instead of it"
            )
        return self
