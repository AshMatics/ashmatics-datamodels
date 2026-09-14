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
Derivations over hazard records (aigov-framework ADR-020 D3, ADR-031 D9).

Three CLF quantities are read from a system's hazard records rather than
stored beside them, the way ``registry.derive.system_class`` is read from the
category triad:

- ``{{system.harmLevel}}`` — :func:`system_harm_level`, the maximum over the
  records;
- the analysis depth a harm level earns — :func:`analysis_depth`;
- ``{{system.riskTier}}`` — :func:`system_risk_tier`, a DEFAULT a site may
  override with a recorded reason.

THE RISK TIER IS DERIVED PER RECORD, THEN MAXIMISED (decision J. Kalafut,
2026-09-14). ADR-031 D9's text reads as "the system's harm level and its
maximum residual P1 × P2", which taken literally pairs the harm of one record
with the probability of another: a catastrophic situation that is nearly
impossible and a trivial one that is frequent would combine into a high tier
neither earns. The unit of scoring is the hazardous situation (ADR-020 D1), so
each record is placed on the table from its OWN harm level and probabilities,
and the system takes the highest tier any record reaches.

THE TABLE IS CHAR'S FIRST CALIBRATION (same decision). P1 and P2 are ordinal
bands, so "P1 × P2" cannot be a product; their ordinal positions are summed
(2–9, the ordinal analogue of multiplying probabilities on a log scale) and
cut into three columns. Severity is never discounted by likelihood (RMP §4.4):
harm level 5 is high in every column and harm level 4 is never low. A site's
own matrix regions govern acceptability; this table governs only the default
tier, and the override is where a site that disagrees says so.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import TYPE_CHECKING

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .enums import (
    P1_ORDINAL,
    P2_ORDINAL,
    AnalysisDepth,
    HarmLevel,
    LikelihoodBand,
    P1Band,
    P2Band,
    RiskTier,
    RiskTierBasis,
)

if TYPE_CHECKING:  # record.py imports this module
    from .record import HazardRecord


_L, _M, _H = RiskTier.LOW, RiskTier.MODERATE, RiskTier.HIGH

DEFAULT_RISK_TIER_TABLE: dict[HarmLevel, dict[LikelihoodBand, RiskTier]] = {
    #                      unlikely                  possible                  likely
    HarmLevel.NEGLIGIBLE: {LikelihoodBand.UNLIKELY: _L, LikelihoodBand.POSSIBLE: _L, LikelihoodBand.LIKELY: _M},
    HarmLevel.MINOR: {LikelihoodBand.UNLIKELY: _L, LikelihoodBand.POSSIBLE: _M, LikelihoodBand.LIKELY: _M},
    HarmLevel.SERIOUS: {LikelihoodBand.UNLIKELY: _M, LikelihoodBand.POSSIBLE: _M, LikelihoodBand.LIKELY: _H},
    HarmLevel.CRITICAL: {LikelihoodBand.UNLIKELY: _M, LikelihoodBand.POSSIBLE: _H, LikelihoodBand.LIKELY: _H},
    HarmLevel.CATASTROPHIC: {LikelihoodBand.UNLIKELY: _H, LikelihoodBand.POSSIBLE: _H, LikelihoodBand.LIKELY: _H},
}
"""(harm level, likelihood band) → default risk tier. Rendered in the
aigov-framework ``WP-RM-01-Risk-Register.md``; this constant is the authored
end, as ``registry.derive.system_class`` is for ``{{system.class}}``."""

_TIER_ORDINAL = {RiskTier.LOW: 1, RiskTier.MODERATE: 2, RiskTier.HIGH: 3}


def analysis_depth(level: HarmLevel | int) -> AnalysisDepth:
    """``harm_model.yaml`` ``analysis_depth``: 1–2 hazard record only, 3
    failure-mode analysis, 4–5 full safety analysis. What a level EARNS; how
    much the organization originates depends on obligation, not on this."""
    level = HarmLevel(level)
    if level <= HarmLevel.MINOR:
        return AnalysisDepth.HAZARD_RECORD_ONLY
    if level is HarmLevel.SERIOUS:
        return AnalysisDepth.FAILURE_MODE_ANALYSIS
    return AnalysisDepth.FULL_SAFETY_ANALYSIS


def likelihood_band(p1: P1Band | str, p2: P2Band | str) -> LikelihoodBand:
    """P1 ordinal (1–5) plus P2 ordinal (1–4): 2–4 unlikely, 5–6 possible,
    7–9 likely."""
    score = P1_ORDINAL[P1Band(p1)] + P2_ORDINAL[P2Band(p2)]
    if score <= 4:
        return LikelihoodBand.UNLIKELY
    if score <= 6:
        return LikelihoodBand.POSSIBLE
    return LikelihoodBand.LIKELY


def risk_tier(level: HarmLevel | int, p1: P1Band | str, p2: P2Band | str) -> RiskTier:
    """One position on :data:`DEFAULT_RISK_TIER_TABLE`."""
    return DEFAULT_RISK_TIER_TABLE[HarmLevel(level)][likelihood_band(p1, p2)]


class RecordRiskTier(AshMaticsBaseModel):
    """A record's default tier and which of its positions it was read from."""

    record_id: str
    tier: RiskTier
    basis: RiskTierBasis


def record_risk_tier(record: HazardRecord) -> RecordRiskTier:
    """The record's residual position once it has one; its initial position
    before that. Reading the initial position of a record whose controls are
    unscored errs high, which is the safe direction for a default."""
    if record.residual is not None:
        pos = record.residual
        tier = risk_tier(pos.harm_level, pos.p1, pos.p2)
        basis = RiskTierBasis.RESIDUAL
    else:
        tier = risk_tier(record.harm.level, record.initial.p1, record.initial.p2)
        basis = RiskTierBasis.INITIAL
    return RecordRiskTier(record_id=record.record_id, tier=tier, basis=basis)


def system_harm_level(records: Iterable[HazardRecord]) -> HarmLevel | None:
    """``{{system.harmLevel}}``: the maximum scored harm level over the records.

    The SCORED level, not the residual one — this attribute sets the depth of
    analysis, which is decided before controls exist. No records derives
    ``None``, never a level: an unanalysed system has no harm level, and
    inventing one would set its depth tier by default.
    """
    levels = [r.harm.level for r in records]
    return HarmLevel(max(levels)) if levels else None


class RiskTierOverride(AshMaticsBaseModel):
    """A site's decision to set a system's tier other than the derived one.

    The reason is required and is the point: the override is kept beside the
    derived value, never in place of it, so a later reader can see both.
    """

    tier: RiskTier
    reason: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    decided_on: date


class RiskTierAssessment(AshMaticsBaseModel):
    """``{{system.riskTier}}`` with its derivation on the record."""

    derived: RiskTier | None = Field(
        ..., description="None when the system has no hazard records."
    )
    governing: list[RecordRiskTier] = Field(
        default_factory=list,
        description="The records that reach the derived tier.",
    )
    override: RiskTierOverride | None = None

    @property
    def effective(self) -> RiskTier | None:
        """What ``{{system.riskTier}}`` resolves to: the override where there is
        one, else the derivation."""
        if self.override is not None:
            return RiskTier(self.override.tier)
        return RiskTier(self.derived) if self.derived is not None else None


def system_risk_tier(
    records: Iterable[HazardRecord],
    override: RiskTierOverride | None = None,
) -> RiskTierAssessment:
    """Per record, then the maximum (see the module docstring for why not the
    ADR's literal reading). ``governing`` names every record at that tier, so a
    reviewer can see which situations set it."""
    per_record = [record_risk_tier(r) for r in records]
    if not per_record:
        return RiskTierAssessment(derived=None, override=override)
    top = max(per_record, key=lambda rt: _TIER_ORDINAL[RiskTier(rt.tier)]).tier
    return RiskTierAssessment(
        derived=top,
        governing=[rt for rt in per_record if rt.tier == top],
        override=override,
    )
