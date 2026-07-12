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

from pydantic import Field

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
    type: Literal["string", "number", "boolean", "array", "object"] = Field(
        ..., description="CLF value type of the resolved attribute."
    )
    source: Literal["ai_inventory", "risk_register"] | None = Field(
        None,
        description="Operational store the value resolves from. Optional "
        "when skos_scheme alone defines the value space (classification "
        "attributes resolve from the inventory's ontology tagging).",
    )
    skos_scheme: str | None = Field(
        None, pattern=CURIE_PATTERN,
        description="SKOS ConceptScheme CURIE constraining legal values "
        "(e.g. ash:AIParadigmScheme); None for plain-typed attributes.",
    )
    note: str | None = Field(
        None, description="Registry annotation, e.g. what the attribute drives."
    )
