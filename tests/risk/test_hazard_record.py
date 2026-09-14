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

"""The hazard record contract against the two worked records, and each
consistency rule broken once."""

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.failure_modes import AIFailureMode
from ashmatics_datamodels.risk import AnalysisDepth, HarmLevel, HazardRecord


class TestWorkedExamples:
    def test_both_records_validate_and_round_trip(self, h01, h07):
        for data in (h01, h07):
            rec = HazardRecord.model_validate(data)
            assert HazardRecord.model_validate(rec.model_dump()) == rec
            assert HazardRecord.model_validate_json(rec.model_dump_json()) == rec

    def test_harm_level_is_the_maximum_not_the_mean(self, h01, h07):
        assert HazardRecord.model_validate(h01).harm_level is HarmLevel.CATASTROPHIC
        # H-07: patient 3, staff 4 — an administrative system reaches 4 on staff.
        assert HazardRecord.model_validate(h07).harm_level is HarmLevel.CRITICAL

    def test_derived_values_are_not_serialized(self, h01):
        dumped = HazardRecord.model_validate(h01).model_dump()
        for derived in ("harm_level", "earned_depth", "failure_modes", "unvalidated_controls"):
            assert derived not in dumped

    def test_failure_modes_are_read_from_the_links(self, h07):
        assert HazardRecord.model_validate(h07).failure_modes == {
            AIFailureMode.CONFABULATION,
            AIFailureMode.AUTOMATION_BIAS,
            AIFailureMode.ALERT_FATIGUE,
        }

    def test_unvalidated_controls_are_queryable(self, h07):
        rec = HazardRecord.model_validate(h07)
        assert [c.tier for c in rec.unvalidated_controls] == ["information_for_safety"]


class TestChainRules:
    def test_record_id_shape(self, h01):
        h01["record_id"] = "HZ-1"
        with pytest.raises(ValidationError, match="record_id"):
            HazardRecord.model_validate(h01)

    def test_sequence_of_events_cannot_be_empty(self, h01):
        h01["sequence_of_events"] = []
        with pytest.raises(ValidationError, match="sequence_of_events"):
            HazardRecord.model_validate(h01)

    def test_failure_mode_must_be_a_taxonomy_class(self, h01):
        h01["sequence_of_events"][1]["failure_mode"] = "fm-model-error"
        with pytest.raises(ValidationError, match="failure_mode"):
            HazardRecord.model_validate(h01)

    def test_every_dimension_is_scored(self, h01):
        del h01["harm"]["staff"]
        with pytest.raises(ValidationError, match="staff"):
            HazardRecord.model_validate(h01)

    def test_harm_level_outside_the_scale(self, h01):
        h01["harm"]["economic"]["level"] = 6
        with pytest.raises(ValidationError):
            HazardRecord.model_validate(h01)

    def test_depth_may_not_be_shallower_than_earned(self, h07):
        h07["depth"]["tier"] = "failure_mode_analysis"
        with pytest.raises(ValidationError, match="shallower"):
            HazardRecord.model_validate(h07)

    def test_depth_may_go_deeper_than_earned(self, h07):
        for dim in h07["harm"].values():
            dim["level"] = 2
        h07["residual"]["harm_level"] = 2
        rec = HazardRecord.model_validate(h07)
        assert rec.earned_depth is AnalysisDepth.HAZARD_RECORD_ONLY
        assert rec.depth.tier == "full_safety_analysis"

    def test_stopping_at_the_record_needs_a_rationale(self, h07):
        for dim in h07["harm"].values():
            dim["level"] = 1
        h07["residual"]["harm_level"] = 1
        h07["depth"]["tier"] = "hazard_record_only"
        with pytest.raises(ValidationError, match="stop_rationale"):
            HazardRecord.model_validate(h07)
        h07["depth"]["stop_rationale"] = "No pathway to a person; rework only."
        HazardRecord.model_validate(h07)

    def test_validation_before_verification(self, h01):
        h01["controls"][0]["verification"] = None
        with pytest.raises(ValidationError, match="before it is verified"):
            HazardRecord.model_validate(h01)

    def test_validation_dated_before_verification(self, h01):
        h01["controls"][0]["validation"]["dated"] = "2026-07-01"
        with pytest.raises(ValidationError, match="precedes"):
            HazardRecord.model_validate(h01)

    def test_residual_p1_fall_needs_a_p1_control(self, h01):
        for c in h01["controls"]:
            c["reduces"] = "p2"
        with pytest.raises(ValidationError, match="no control reduces P1"):
            HazardRecord.model_validate(h01)

    def test_residual_p2_fall_needs_a_p2_control(self, h07):
        for c in h07["controls"]:
            c["reduces"] = "p1"
        with pytest.raises(ValidationError, match="no control reduces P2"):
            HazardRecord.model_validate(h07)

    def test_unchanged_p_needs_no_control(self, h01):
        # H-01 leaves P2 at moderate; its one P2 control is information for
        # safety. Removing it must not trip the P2 rule.
        h01["controls"] = h01["controls"][:2]
        HazardRecord.model_validate(h01)

    def test_residual_harm_cannot_exceed_scored_harm(self, h07):
        h07["residual"]["harm_level"] = 5
        with pytest.raises(ValidationError, match="exceeds the scored harm"):
            HazardRecord.model_validate(h07)

    def test_acceptance_needs_a_residual_position(self, h01):
        h01["residual"] = None
        with pytest.raises(ValidationError, match="residual position first"):
            HazardRecord.model_validate(h01)

    def test_unacceptable_is_never_accepted(self, h01):
        h01["acceptance"]["outcome"] = "unacceptable"
        with pytest.raises(ValidationError, match="not accepted by anyone"):
            HazardRecord.model_validate(h01)

    def test_revisit_must_follow_acceptance(self, h01):
        h01["acceptance"]["revisit_on"] = h01["acceptance"]["accepted_on"]
        with pytest.raises(ValidationError, match="revisit_on"):
            HazardRecord.model_validate(h01)

    def test_tolerable_is_not_accepted_until_something_watches_it(self, h07):
        h07["watched_items"] = []
        with pytest.raises(ValidationError, match="watched_items is empty"):
            HazardRecord.model_validate(h07)
        h07["acceptance"]["outcome"] = "acceptable"
        HazardRecord.model_validate(h07)

    def test_unknown_fields_are_rejected(self, h01):
        h01["risk_score"] = 20
        with pytest.raises(ValidationError, match="risk_score"):
            HazardRecord.model_validate(h01)
