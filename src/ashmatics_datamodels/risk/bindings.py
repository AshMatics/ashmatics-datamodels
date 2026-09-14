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
Ontology-anchoring declarations for the hazard chain vocabularies (ADR-002).

Same table shape and status vocabulary as ``registry.bindings``; the guard is
``tests/risk/test_ontology_binding.py``. One vocabulary is anchored; the rest
are recorded as decisions rather than left unanchored by default.
"""

from ashmatics_datamodels.common.enums import SignalAccess
from ashmatics_datamodels.registry.bindings import BindingStatus, SchemeBinding

from .enums import (
    Acceptability,
    AnalysisDepth,
    ControlTier,
    HarmDimension,
    HarmLevel,
    LikelihoodBand,
    P1Band,
    P2Band,
    ProbabilityReduced,
    RiskTier,
    RiskTierBasis,
)

_CHAR_CONTENT = (
    "CHAR content vocabulary authored in the aigov-framework ({src}); no "
    "ontology scheme minted. A graph that needs to reason over it mints the "
    "scheme then and flips this row, the way SignalAccessScheme was minted "
    "when {{{{system.signalAccess}}}} needed one."
)

RISK_BINDINGS: tuple[SchemeBinding, ...] = (
    SchemeBinding(
        enum=RiskTier,
        status=BindingStatus.BOUND,
        scheme="ash:RiskTierScheme",
        note="Members match ash:risk-* skos:notation (CLF system.riskTier).",
    ),
    SchemeBinding(
        enum=SignalAccess,
        status=BindingStatus.BOUND,
        scheme="ash:SignalAccessScheme",
        note=(
            "Members match ash:sig-* skos:notation (ontology 0.18.0 / 2.11.0, "
            "ADR-031 D5). Defined in common.enums as a system facet; declared "
            "here because the hazard chain is what introduced it."
        ),
    ),
    SchemeBinding(
        enum=HarmLevel,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="harm_model.yaml scale"),
    ),
    SchemeBinding(
        enum=HarmDimension,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="harm_model.yaml dimensions"),
    ),
    SchemeBinding(
        enum=AnalysisDepth,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="harm_model.yaml analysis_depth"),
    ),
    SchemeBinding(
        enum=P1Band,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="RMP §4.3"),
    ),
    SchemeBinding(
        enum=P2Band,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="RMP §4.3"),
    ),
    SchemeBinding(
        enum=Acceptability,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="RMP §5.2"),
    ),
    SchemeBinding(
        enum=ControlTier,
        status=BindingStatus.PRODUCT,
        note=_CHAR_CONTENT.format(src="RMP §6, ISO 14971 order"),
    ),
    SchemeBinding(
        enum=ProbabilityReduced,
        status=BindingStatus.PRODUCT,
        note="Record shape (which of P1/P2 a control reduces), not a concept.",
    ),
    SchemeBinding(
        enum=LikelihoodBand,
        status=BindingStatus.PRODUCT,
        note="Columns of the default risk tier table; derivation vocabulary only.",
    ),
    SchemeBinding(
        enum=RiskTierBasis,
        status=BindingStatus.PRODUCT,
        note="Which record position a derived tier was read from; derivation vocabulary only.",
    ),
)
