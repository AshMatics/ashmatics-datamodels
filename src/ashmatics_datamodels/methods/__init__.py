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
CHAR governance-method contracts (aigov-framework ADR-011, ASHKBAPP-99).

The method stratum of the CHAR vocabulary spine: exemplar method
definitions with SKOS-bound applicability, shared method sets, the
client-approved variant, and the CLF v0.6.0 rule-grammar extensions shared
with coreapp MethodRoute (ADR-031).

Usage::

    from ashmatics_datamodels.methods import (
        MethodRegistry,
        MethodDefinition,
        ApplicabilityProfile,
        MethodSet,
        ApprovedMethodSet,
        SystemAttribute,
    )
"""

from .clf import SystemAttribute
from .enums import (
    AIParadigm,
    ConditionScope,
    DeliveryMode,
    EvaluationTime,
    EvidenceType,
    FairnessFactor,
    InputModality,
    MethodControlAction,
    MethodFamily,
    MethodPhase,
    ModelClass,
    OutputForm,
    RobustnessFactor,
)
from .method_sets import (
    ApprovedMethodSet,
    JunctionBinding,
    MethodSet,
    MethodSetAdjustment,
)
from .methods import (
    JUNCTION_REF_PATTERN,
    METHOD_ID_PATTERN,
    METHOD_SET_ID_PATTERN,
    POLICY_TOKEN_PATTERN,
    TOOL_TOKEN_PATTERN,
    ApplicabilityProfile,
    DefaultRule,
    EvidenceRef,
    MethodDefinition,
    MethodReview,
)
from .registry import MethodRegistry, RegistryMetadata

__all__ = [
    # document
    "MethodRegistry",
    "RegistryMetadata",
    # methods
    "MethodDefinition",
    "ApplicabilityProfile",
    "EvidenceRef",
    "DefaultRule",
    "MethodReview",
    # sets
    "MethodSet",
    "ApprovedMethodSet",
    "JunctionBinding",
    "MethodSetAdjustment",
    # CLF
    "SystemAttribute",
    "ConditionScope",
    "EvaluationTime",
    "MethodControlAction",
    # enums
    "MethodFamily",
    "MethodPhase",
    "EvidenceType",
    "DeliveryMode",
    "AIParadigm",
    "OutputForm",
    "InputModality",
    "FairnessFactor",
    "RobustnessFactor",
    "ModelClass",
    # ID grammars
    "METHOD_ID_PATTERN",
    "METHOD_SET_ID_PATTERN",
    "JUNCTION_REF_PATTERN",
    "TOOL_TOKEN_PATTERN",
    "POLICY_TOKEN_PATTERN",
]
