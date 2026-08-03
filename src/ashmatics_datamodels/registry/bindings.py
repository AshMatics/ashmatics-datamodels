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
Ontology-anchoring declarations for the registry vocabularies (ADR-002).

The org module hangs ``x_ontology_*`` annotations on Pydantic model fields;
the registry vocabularies have no Pydantic contract yet (the persisted shape
is coreapp's Django model per ADR-036), so the bindings live in this table and
``tests/registry/test_ontology_binding.py`` iterates it directly. Same intent,
same CI teeth: drift between an enum and its scheme is a failed test, not a
silent bug.

Status vocabulary:

- ``BOUND``   — the scheme exists in the ontology; the guard enforces every
  member (minus declared extras) is a concept of it.
- ``PENDING`` — the anchor is being authored in ashmatics-ontology; the guard
  skips loudly so the gap stays visible in every test run. Flip to ``BOUND``
  with the scheme CURIE the moment the scheme lands.
- ``PRODUCT`` — deliberately product-level vocabulary with no anchor planned;
  recorded so "unanchored" is always a decision, never an oversight.
"""

from dataclasses import dataclass, field
from enum import Enum

from .enums import (
    OrgSourcingMix,
    PortfolioSizeBucket,
    RegistryAIType,
    RegistryCategory,
    RegistryDeployment,
    RegistrySourcing,
)


class BindingStatus(str, Enum):
    BOUND = "bound"
    PENDING = "pending"
    PRODUCT = "product"


@dataclass(frozen=True)
class SchemeBinding:
    """One vocabulary's anchoring declaration.

    ``extra_members`` are product escape values with no concept in the scheme
    (e.g. ``other``). The guard asserts they are absent from the scheme too —
    if the ontology later grows a matching concept, the carve-out must be
    retired, and that test failure is the reminder.
    """

    enum: type[Enum]
    status: BindingStatus
    scheme: str | None = None  # CURIE, e.g. "ash:AIParadigmScheme"
    extra_members: frozenset[str] = field(default_factory=frozenset)
    note: str = ""


REGISTRY_BINDINGS: tuple[SchemeBinding, ...] = (
    SchemeBinding(
        enum=RegistryAIType,
        status=BindingStatus.BOUND,
        scheme="ash:AIParadigmScheme",
        extra_members=frozenset({"other"}),
        note=(
            "Members match ash:ap-* skos:notation. 'other' is a UI collapse of "
            "the scheme's finer paradigms (forecasting, hybrid, neurosymbolic, "
            "rule-based, causal)."
        ),
    ),
    SchemeBinding(
        enum=RegistryCategory,
        status=BindingStatus.PENDING,
        note=(
            "Anchor = the top-level clinical/operational/administrative "
            "scope-zone triad being authored in ashmatics-ontology alongside "
            "ash:OperationalPurposeScheme (where the three boundary cp-* "
            "concepts — cp-documentation, cp-care-coordination, "
            "cp-prior-authorization — migrate). ASHFORGE-412."
        ),
    ),
    SchemeBinding(
        enum=RegistrySourcing,
        status=BindingStatus.PRODUCT,
        note=(
            "Encodes where the validation obligation sits (SRS-REG-15a); no "
            "ontology axis exists for this and none is planned."
        ),
    ),
    SchemeBinding(
        enum=RegistryDeployment,
        status=BindingStatus.PRODUCT,
        note=(
            "Integration topology. Product vocabulary today; revisit if ash: "
            "ever grows a deployment axis."
        ),
    ),
    SchemeBinding(
        enum=PortfolioSizeBucket,
        status=BindingStatus.PRODUCT,
        note="Derived vocabulary (AC-3); presentation of a count, not a concept.",
    ),
    SchemeBinding(
        enum=OrgSourcingMix,
        status=BindingStatus.PRODUCT,
        note="Derived vocabulary (AC-3); proportion rollup, not a concept.",
    ),
)
