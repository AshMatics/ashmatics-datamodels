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
The CHAR hazard chain (aigov-framework ADR-020, ADR-031).

The hazard record contract, the vocabularies it is scored on, and the
derivations that read ``{{system.harmLevel}}`` and ``{{system.riskTier}}`` from
a system's records.

    from ashmatics_datamodels.risk import (
        HazardRecord,
        HarmLevel,
        P1Band,
        P2Band,
        system_harm_level,
        system_risk_tier,
    )
"""

from .bindings import RISK_BINDINGS
from .derive import (
    DEFAULT_RISK_TIER_TABLE,
    RecordRiskTier,
    RiskTierAssessment,
    RiskTierOverride,
    analysis_depth,
    likelihood_band,
    record_risk_tier,
    risk_tier,
    system_harm_level,
    system_risk_tier,
)
from .enums import (
    DEPTH_ORDINAL,
    P1_ORDINAL,
    P2_ORDINAL,
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
from .record import (
    DepthAssignment,
    DimensionHarm,
    EventLink,
    Evidence,
    HarmAssessment,
    HazardRecord,
    ProbabilityPosition,
    ResidualAcceptance,
    ResidualPosition,
    RiskControl,
)

__all__ = [
    # record
    "HazardRecord",
    "EventLink",
    "DimensionHarm",
    "HarmAssessment",
    "DepthAssignment",
    "ProbabilityPosition",
    "Evidence",
    "RiskControl",
    "ResidualPosition",
    "ResidualAcceptance",
    # vocabularies
    "HarmLevel",
    "HarmDimension",
    "AnalysisDepth",
    "P1Band",
    "P2Band",
    "Acceptability",
    "ControlTier",
    "ProbabilityReduced",
    "RiskTier",
    "LikelihoodBand",
    "RiskTierBasis",
    "P1_ORDINAL",
    "P2_ORDINAL",
    "DEPTH_ORDINAL",
    # derivations
    "analysis_depth",
    "likelihood_band",
    "risk_tier",
    "record_risk_tier",
    "system_harm_level",
    "system_risk_tier",
    "RecordRiskTier",
    "RiskTierAssessment",
    "RiskTierOverride",
    "DEFAULT_RISK_TIER_TABLE",
    "RISK_BINDINGS",
]
