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

"""The ADR-031 D9 derivations: harm level, depth, and the risk tier with
override."""

from datetime import date

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.common.enums import RiskCategory
from ashmatics_datamodels.risk import (
    DEFAULT_RISK_TIER_TABLE,
    P1_ORDINAL,
    P2_ORDINAL,
    AnalysisDepth,
    HarmLevel,
    HazardRecord,
    LikelihoodBand,
    P1Band,
    P2Band,
    RiskTier,
    RiskTierBasis,
    RiskTierOverride,
    analysis_depth,
    likelihood_band,
    record_risk_tier,
    risk_tier,
    system_harm_level,
    system_risk_tier,
)

TIER_ORDER = [RiskTier.LOW, RiskTier.MODERATE, RiskTier.HIGH]


def _unscored_record(record_id: str, *, level: int, p1: str, p2: str) -> HazardRecord:
    """A record at its initial position, harm ``level`` on every dimension."""
    depth = {"tier": analysis_depth(level).value, "obligation": "vendor"}
    if level <= 2:
        depth["stop_rationale"] = "illustrative"
    return HazardRecord.model_validate(
        {
            "record_id": record_id,
            "hazard": "h",
            "sequence_of_events": [{"description": "e"}],
            "hazardous_situation": "s",
            "harm": {d: {"level": level} for d in ("patient", "staff", "economic", "reputational")},
            "depth": depth,
            "initial": {"p1": p1, "p2": p2},
            "acceptability_initial": "tolerable",
        }
    )


class TestAnalysisDepth:
    @pytest.mark.parametrize(
        ("level", "depth"),
        [
            (1, AnalysisDepth.HAZARD_RECORD_ONLY),
            (2, AnalysisDepth.HAZARD_RECORD_ONLY),
            (3, AnalysisDepth.FAILURE_MODE_ANALYSIS),
            (4, AnalysisDepth.FULL_SAFETY_ANALYSIS),
            (5, AnalysisDepth.FULL_SAFETY_ANALYSIS),
        ],
    )
    def test_harm_model_thresholds(self, level, depth):
        assert analysis_depth(level) is depth

    def test_out_of_scale(self):
        with pytest.raises(ValueError):
            analysis_depth(0)


class TestTable:
    def test_table_is_total(self):
        assert set(DEFAULT_RISK_TIER_TABLE) == set(HarmLevel)
        for row in DEFAULT_RISK_TIER_TABLE.values():
            assert set(row) == set(LikelihoodBand)

    def test_the_decided_table(self):
        """The table J. Kalafut chose on 2026-09-14, cell for cell. A change
        here is a CHAR content decision and moves the Register WP with it."""
        L, M, H = "low", "moderate", "high"
        expected = {
            1: (L, L, M),
            2: (L, M, M),
            3: (M, M, H),
            4: (M, H, H),
            5: (H, H, H),
        }
        cols = (LikelihoodBand.UNLIKELY, LikelihoodBand.POSSIBLE, LikelihoodBand.LIKELY)
        for level, row in expected.items():
            assert tuple(DEFAULT_RISK_TIER_TABLE[HarmLevel(level)][c].value for c in cols) == row

    def test_monotone_in_harm_and_likelihood(self):
        cols = list(LikelihoodBand)
        for i, level in enumerate(HarmLevel):
            for j, col in enumerate(cols):
                here = TIER_ORDER.index(DEFAULT_RISK_TIER_TABLE[level][col])
                if i:
                    below = DEFAULT_RISK_TIER_TABLE[HarmLevel(level - 1)][col]
                    assert TIER_ORDER.index(below) <= here
                if j:
                    left = DEFAULT_RISK_TIER_TABLE[level][cols[j - 1]]
                    assert TIER_ORDER.index(left) <= here

    def test_severity_is_never_discounted(self):
        """RMP §4.4: catastrophic is high in every column; critical never low."""
        for p1 in P1Band:
            for p2 in P2Band:
                assert risk_tier(5, p1, p2) is RiskTier.HIGH
                assert risk_tier(4, p1, p2) is not RiskTier.LOW

    @pytest.mark.parametrize(
        ("p1", "p2", "band"),
        [
            ("improbable", "very_low", LikelihoodBand.UNLIKELY),  # 2
            ("occasional", "very_low", LikelihoodBand.UNLIKELY),  # 4
            ("remote", "moderate", LikelihoodBand.POSSIBLE),  # 5
            ("frequent", "very_low", LikelihoodBand.POSSIBLE),  # 6
            ("improbable", "high", LikelihoodBand.POSSIBLE),  # 5
            ("probable", "moderate", LikelihoodBand.LIKELY),  # 7
            ("frequent", "high", LikelihoodBand.LIKELY),  # 9
        ],
    )
    def test_likelihood_cut_points(self, p1, p2, band):
        assert likelihood_band(p1, p2) is band

    def test_ordinals_are_complete_and_dense(self):
        assert sorted(P1_ORDINAL.values()) == [1, 2, 3, 4, 5]
        assert sorted(P2_ORDINAL.values()) == [1, 2, 3, 4]
        assert set(P1_ORDINAL) == set(P1Band)
        assert set(P2_ORDINAL) == set(P2Band)


class TestRecordAndSystem:
    def test_worked_examples(self, h01, h07):
        r1, r7 = HazardRecord.model_validate(h01), HazardRecord.model_validate(h07)
        # H-01 residual: harm 5, remote + moderate = 5 → possible → high.
        assert record_risk_tier(r1).tier == "high"
        # H-07 residual: harm 4, improbable + low = 3 → unlikely → moderate.
        assert record_risk_tier(r7).tier == "moderate"
        assert record_risk_tier(r7).basis == RiskTierBasis.RESIDUAL

    def test_initial_position_before_controls_are_scored(self, h07):
        h07["residual"] = None
        h07["acceptance"] = None
        rt = record_risk_tier(HazardRecord.model_validate(h07))
        # harm 4, occasional + high = 7 → likely → high: errs high.
        assert (rt.tier, rt.basis) == ("high", "initial")

    def test_per_record_not_cross_paired(self):
        """The decision this module documents. A serious situation that is
        improbable and a negligible one that is frequent must not combine into
        a high tier neither earns."""
        serious_rare = _unscored_record("H-03", level=3, p1="improbable", p2="very_low")
        trivial_frequent = _unscored_record("H-04", level=1, p1="frequent", p2="high")

        # Read the ADR literally: max harm 3 with max likelihood → high.
        assert risk_tier(3, "frequent", "high") is RiskTier.HIGH
        # Per record: harm 3 unlikely → moderate; harm 1 likely → moderate.
        assessment = system_risk_tier([serious_rare, trivial_frequent])
        assert assessment.derived == "moderate"
        assert [g.record_id for g in assessment.governing] == ["H-03", "H-04"]

    def test_system_takes_the_highest_and_names_it(self, h01, h07):
        records = [HazardRecord.model_validate(h07), HazardRecord.model_validate(h01)]
        assessment = system_risk_tier(records)
        assert assessment.derived == "high"
        assert [g.record_id for g in assessment.governing] == ["H-01"]
        assert assessment.effective is RiskTier.HIGH
        assert system_harm_level(records) is HarmLevel.CATASTROPHIC

    def test_no_records_derives_nothing(self):
        assert system_harm_level([]) is None
        assessment = system_risk_tier([])
        assert assessment.derived is None and assessment.effective is None

    def test_override_is_kept_beside_the_derivation(self, h07):
        override = RiskTierOverride(
            tier="high",
            reason="Denials land on a protected group; the committee holds this high regardless.",
            author="AI governance committee",
            decided_on=date(2026, 9, 14),
        )
        assessment = system_risk_tier([HazardRecord.model_validate(h07)], override)
        assert assessment.derived == "moderate"
        assert assessment.effective is RiskTier.HIGH
        assert assessment.model_dump()["derived"] == "moderate"

    def test_override_needs_a_reason(self):
        with pytest.raises(ValidationError, match="reason"):
            RiskTierOverride(tier="low", reason="", author="x", decided_on=date(2026, 9, 14))

    def test_system_harm_level_reads_scored_not_residual(self, h07):
        h07["residual"]["harm_level"] = 2
        assert system_harm_level([HazardRecord.model_validate(h07)]) is HarmLevel.CRITICAL


def test_risk_tier_is_not_the_device_class_risk():
    """RiskCategory is the FDA device-class risk; RiskTier is derived from
    hazard records. Same spellings, different concepts (ADR-020 D8). Merging
    them, or aliasing one to the other, is the conflation ontology 0.18.1
    removed."""
    assert RiskTier is not RiskCategory
    assert not issubclass(RiskTier, RiskCategory) and not issubclass(RiskCategory, RiskTier)
    assert RiskTier.__module__ == "ashmatics_datamodels.risk.enums"
