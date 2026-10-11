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
The sub-models the hazard and risk application needs (0.21.0, ASHFORGE-827,
coreapp ADR-061 D3 and D9, ADR-062 D3).

Each addition is tested three ways: present and valid, ABSENT and valid (the
two worked records in ``conftest.py`` are untouched from 0.16.0 and are the
proof that every earlier payload still validates), and the invalid shape
refused. The records are the framework's worked examples, extended in each test
by one field.
"""

import json

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.common.enums import SignalAccess
from ashmatics_datamodels.failure_modes import AIFailureMode
from ashmatics_datamodels.risk import (
    AnalysisDepth,
    DimensionHarm,
    EventLink,
    FailureAnalysisEntry,
    FailureClassScreening,
    FailureClassScreeningSet,
    FailureWatchListRow,
    HarmAssessment,
    HarmLevel,
    HazardRecord,
    LinkType,
    system_harm_level,
)


def _round_trips(rec: HazardRecord) -> None:
    assert HazardRecord.model_validate(rec.model_dump()) == rec
    assert HazardRecord.model_validate_json(rec.model_dump_json()) == rec


def _row(**over) -> dict:
    row = {
        "failure_mode": "fm-silent-incompetence",
        "max_harm_level": 5,
        "observable": "eligible-to-scored coverage ratio per site",
        "source": "scoring service log",
        "acquisition_mode": "queried",
        "cadence": "daily",
        "threshold": "below 0.98 for two consecutive days",
        "owner": "PACS administrator",
    }
    row.update(over)
    return row


class TestEarlierPayloadsStillValidate:
    """The compatibility claim of a minor bump, stated as a test."""

    def test_the_worked_records_carry_none_of_the_new_fields(self, h01, h07):
        new = {"method_used", "method_rationale_ref", "failure_analysis"}
        for data in (h01, h07):
            assert not new & data.keys()
            assert all("link_type" not in e for e in data["sequence_of_events"])
            assert all(
                "not_reachable" not in d and "not_reachable_reason" not in d
                for d in data["harm"].values()
            )
            assert all(isinstance(w, str) for w in data["watched_items"])

    def test_both_validate_and_read_as_before(self, h01, h07):
        r1, r7 = HazardRecord.model_validate(h01), HazardRecord.model_validate(h07)
        assert r1.harm_level is HarmLevel.CATASTROPHIC
        assert r7.harm_level is HarmLevel.CRITICAL
        assert r1.method_used is None and r1.method_rationale_ref is None
        assert r1.failure_analysis == []
        assert r1.watched_items == ["S-01", "S-02"]
        assert r1.watch_list_rows == []
        assert r1.watched_item_ids == ["S-01", "S-02"]
        _round_trips(r1)
        _round_trips(r7)

    def test_bare_ids_dump_as_bare_ids(self, h01):
        dumped = HazardRecord.model_validate(h01).model_dump()
        assert dumped["watched_items"] == ["S-01", "S-02"]


class TestMethodUsed:
    def test_a_registered_shaped_id_validates(self, h01):
        h01["method_used"] = "mth://hazard.stpa"
        h01["method_rationale_ref"] = "evt-0042"
        rec = HazardRecord.model_validate(h01)
        assert rec.method_used == "mth://hazard.stpa"
        assert rec.method_rationale_ref == "evt-0042"
        _round_trips(rec)

    def test_the_six_ids_are_not_hard_coded(self, h01):
        # Shape only. An id the registry does not hold yet validates; whether
        # it is registered is the consumer's check against the mirror.
        h01["method_used"] = "mth://anything.at_all_2"
        HazardRecord.model_validate(h01)

    def test_absent_and_none_validate(self, h01):
        assert HazardRecord.model_validate(h01).method_used is None
        h01["method_used"] = None
        h01["method_rationale_ref"] = None
        rec = HazardRecord.model_validate(h01)
        assert rec.method_used is None
        _round_trips(rec)

    @pytest.mark.parametrize(
        "bad",
        [
            "hazard.stpa",  # no scheme
            "http://hazard.stpa",
            "mth://",  # prefix alone
            "mth://stpa",  # no family
            "mth://Hazard.STPA",  # the registry's ids are lower case
            "MTH://hazard.stpa",
            "mth://hazard.stpa ids",
            "",
        ],
    )
    def test_bad_shapes_are_refused(self, h01, bad):
        h01["method_used"] = bad
        with pytest.raises(ValidationError, match="method_used"):
            HazardRecord.model_validate(h01)

    def test_rationale_ref_cannot_be_empty(self, h01):
        h01["method_used"] = "mth://hazard.fmea"
        h01["method_rationale_ref"] = ""
        with pytest.raises(ValidationError, match="method_rationale_ref"):
            HazardRecord.model_validate(h01)

    def test_a_scheme_annotation_is_on_the_field(self):
        extra = HazardRecord.model_fields["method_used"].json_schema_extra
        assert extra == {"x_ontology_scheme": "ashcai:GovernanceMethodScheme"}


class TestLinkType:
    @pytest.mark.parametrize("value", ["technical", "human", "organizational"])
    def test_each_type_validates(self, h01, value):
        h01["sequence_of_events"][0]["link_type"] = value
        rec = HazardRecord.model_validate(h01)
        assert rec.sequence_of_events[0].link_type == value
        _round_trips(rec)

    def test_absent_validates_and_is_none(self, h01):
        rec = HazardRecord.model_validate(h01)
        assert all(link.link_type is None for link in rec.sequence_of_events)

    def test_a_link_can_be_typed_with_or_without_a_failure_mode(self):
        EventLink(
            description="A reader reads absence as a negative.", link_type="human"
        )
        EventLink(
            description="Never scored.",
            failure_mode="fm-silent-incompetence",
            link_type=LinkType.TECHNICAL,
        )

    @pytest.mark.parametrize("bad", ["political", "organisational", "", "Human"])
    def test_an_unknown_type_is_refused(self, h01, bad):
        h01["sequence_of_events"][0]["link_type"] = bad
        with pytest.raises(ValidationError, match="link_type"):
            HazardRecord.model_validate(h01)


class TestNotReachable:
    NR = {"not_reachable": True, "not_reachable_reason": "No pathway to staff."}

    def test_scored_dimensions_are_unchanged(self):
        d = DimensionHarm(level=3, rationale="A reader held to a read.")
        assert d.level == 3 and d.not_reachable is False
        assert d.not_reachable_reason is None

    def test_a_dimension_can_be_not_reachable_with_a_reason(self, h07):
        h07["harm"]["staff"] = dict(self.NR)
        rec = HazardRecord.model_validate(h07)
        assert rec.harm.staff.level is None
        assert rec.harm.staff.not_reachable is True
        assert rec.harm.staff.not_reachable_reason == "No pathway to staff."
        _round_trips(rec)

    def test_not_reachable_requires_a_reason(self, h07):
        h07["harm"]["staff"] = {"not_reachable": True}
        with pytest.raises(ValidationError, match="not_reachable_reason"):
            HazardRecord.model_validate(h07)

    def test_a_blank_reason_is_no_reason(self, h07):
        h07["harm"]["staff"] = {"not_reachable": True, "not_reachable_reason": "  "}
        with pytest.raises(ValidationError, match="not_reachable_reason"):
            HazardRecord.model_validate(h07)

    def test_a_not_reachable_dimension_has_no_level(self, h07):
        h07["harm"]["staff"] = {"level": 4, **self.NR}
        with pytest.raises(ValidationError, match="has no level"):
            HazardRecord.model_validate(h07)

    def test_a_dimension_is_never_blank(self, h07):
        h07["harm"]["staff"] = {"rationale": "Not yet scored."}
        with pytest.raises(ValidationError, match="never left blank"):
            HazardRecord.model_validate(h07)
        h07["harm"]["staff"] = {}
        with pytest.raises(ValidationError, match="never left blank"):
            HazardRecord.model_validate(h07)

    def test_a_reason_without_the_flag_is_refused(self, h07):
        h07["harm"]["staff"] = {"level": 4, "not_reachable_reason": "Because."}
        with pytest.raises(ValidationError, match="only for a dimension"):
            HazardRecord.model_validate(h07)

    def test_the_dimension_still_has_to_be_present(self, h07):
        del h07["harm"]["staff"]
        with pytest.raises(ValidationError, match="staff"):
            HazardRecord.model_validate(h07)

    def test_a_not_reachable_dimension_does_not_enter_the_maximum(self, h07):
        # H-07 scores patient 3, staff 4, economic 3, reputational 4: critical.
        # Record both level-4 dimensions as not reachable and the maximum is
        # what remains, 3, not 4 and not a zero read from a blank.
        h07["harm"]["staff"] = dict(self.NR)
        h07["harm"]["reputational"] = {
            "not_reachable": True,
            "not_reachable_reason": "Internal workflow; nothing public.",
        }
        h07["residual"]["harm_level"] = 3
        h07["depth"]["tier"] = "failure_mode_analysis"
        rec = HazardRecord.model_validate(h07)
        assert rec.harm_level is HarmLevel.SERIOUS
        assert rec.earned_depth is AnalysisDepth.FAILURE_MODE_ANALYSIS
        assert system_harm_level([rec]) is HarmLevel.SERIOUS

    def test_the_derived_rules_read_the_reduced_maximum(self, h07):
        # With the level-4 dimensions not reachable the scored harm is 3, so a
        # residual harm level of 4 now exceeds it: the existing rule, fed the
        # reduced maximum.
        h07["harm"]["staff"] = dict(self.NR)
        h07["harm"]["reputational"] = dict(self.NR)
        with pytest.raises(ValidationError, match="exceeds the scored harm"):
            HazardRecord.model_validate(h07)

    def test_the_depth_rule_reads_the_reduced_maximum_too(self, h01):
        # H-01 earns full analysis from patient 5. Take patient out and the
        # rest still reach 4 (reputational), so the depth stays earned; take
        # reputational out as well and the remaining 3 earns less than the
        # record's tier, which is allowed (deeper is permitted, shallower not).
        h01["harm"]["patient"] = dict(self.NR)
        h01["residual"]["harm_level"] = 4
        assert HazardRecord.model_validate(h01).harm_level is HarmLevel.CRITICAL
        h01["harm"]["reputational"] = dict(self.NR)
        h01["residual"]["harm_level"] = 3
        rec = HazardRecord.model_validate(h01)
        assert rec.harm_level is HarmLevel.SERIOUS
        assert rec.depth.tier == "full_safety_analysis"

    def test_the_other_scored_dimensions_set_the_level_exactly_as_before(self, h01):
        assert HarmAssessment.model_validate(h01["harm"]).level == 5

    def test_all_four_not_reachable_is_refused(self, h07):
        for dim in ("patient", "staff", "economic", "reputational"):
            h07["harm"][dim] = dict(self.NR)
        with pytest.raises(ValidationError, match="reaches at least one"):
            HazardRecord.model_validate(h07)

    def test_assignment_is_validated_so_a_dimension_is_replaced_whole(self, h07):
        rec = HazardRecord.model_validate(h07)
        with pytest.raises(ValidationError):
            rec.harm.staff.not_reachable = True  # still carries a level
        rec.harm.staff = DimensionHarm(**self.NR)
        assert rec.harm.staff.level is None
        assert rec.harm_level is HarmLevel.CRITICAL  # reputational still 4


class TestFailureClassScreening:
    def _screening(self, **over) -> dict:
        s = {
            "failure_mode": "fm-confabulation",
            "credible": True,
            "reason": "The agent drafts citations from a policy corpus.",
        }
        s.update(over)
        return s

    def test_valid_with_only_the_required_fields(self):
        s = FailureClassScreening.model_validate(self._screening())
        assert s.credible is True
        assert s.no_detection is False
        assert s.evidence_refs == []

    def test_a_class_ruled_out_carries_its_reason(self):
        s = FailureClassScreening.model_validate(
            self._screening(
                failure_mode="fm-alert-fatigue",
                credible=False,
                reason="The system raises no alerts.",
            )
        )
        assert s.credible is False

    def test_flag_and_evidence_refs(self):
        s = FailureClassScreening.model_validate(
            self._screening(
                no_detection=True,
                evidence_refs=[
                    {"type": "doi", "ref": "10.0000/example", "note": "omission"}
                ],
            )
        )
        assert s.no_detection is True
        assert s.evidence_refs[0].type == "doi"
        assert FailureClassScreening.model_validate(s.model_dump()) == s

    def test_every_taxonomy_class_is_accepted(self):
        for mode in AIFailureMode:
            FailureClassScreening.model_validate(
                self._screening(failure_mode=mode.value)
            )

    @pytest.mark.parametrize("missing", ["failure_mode", "credible", "reason"])
    def test_required_fields(self, missing):
        data = self._screening()
        del data[missing]
        with pytest.raises(ValidationError, match=missing):
            FailureClassScreening.model_validate(data)

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_the_reason_is_required_either_way(self, reason):
        for credible in (True, False):
            with pytest.raises(ValidationError, match="reason"):
                FailureClassScreening.model_validate(
                    self._screening(credible=credible, reason=reason)
                )

    @pytest.mark.parametrize(
        "bad", ["fm-omission", "fm-model-error", "confabulation", ""]
    )
    def test_an_unknown_class_is_refused(self, bad):
        # fm-omission is the spec's class that CHAR folded away (ADR-061 D8).
        with pytest.raises(ValidationError, match="failure_mode"):
            FailureClassScreening.model_validate(self._screening(failure_mode=bad))

    def test_a_malformed_evidence_ref_is_refused(self):
        with pytest.raises(ValidationError, match="evidence_refs"):
            FailureClassScreening.model_validate(
                self._screening(evidence_refs=[{"type": "blog", "ref": "x"}])
            )

    def test_unknown_fields_are_rejected(self):
        with pytest.raises(ValidationError, match="severity"):
            FailureClassScreening.model_validate(self._screening(severity=3))


class TestFailureClassScreeningSet:
    def _entry(self, mode: AIFailureMode, credible: bool = True) -> dict:
        return {"failure_mode": mode.value, "credible": credible, "reason": "Because."}

    def test_an_empty_screen_is_a_valid_start(self):
        s = FailureClassScreeningSet()
        assert s.screenings == []
        assert not s.is_complete
        assert s.unscreened_classes == list(AIFailureMode)

    def test_a_partial_screen_is_storable_and_says_what_is_left(self):
        s = FailureClassScreeningSet.model_validate(
            {
                "screenings": [
                    self._entry(AIFailureMode.CONFABULATION),
                    self._entry(AIFailureMode.ALERT_FATIGUE, credible=False),
                ]
            }
        )
        assert s.credible_classes == {AIFailureMode.CONFABULATION}
        assert AIFailureMode.CONFABULATION not in s.unscreened_classes
        assert AIFailureMode.ALERT_FATIGUE not in s.unscreened_classes
        assert len(s.unscreened_classes) == len(AIFailureMode) - 2
        assert not s.is_complete

    def test_one_entry_per_class_for_all_ten_is_complete(self):
        s = FailureClassScreeningSet.model_validate(
            {"screenings": [self._entry(m) for m in AIFailureMode]}
        )
        assert s.is_complete and s.unscreened_classes == []
        assert FailureClassScreeningSet.model_validate_json(s.model_dump_json()) == s

    def test_a_class_screened_twice_is_refused(self):
        with pytest.raises(ValidationError, match="screened twice"):
            FailureClassScreeningSet.model_validate(
                {
                    "screenings": [
                        self._entry(AIFailureMode.CONFABULATION),
                        self._entry(AIFailureMode.CONFABULATION, credible=False),
                    ]
                }
            )

    def test_a_bad_entry_inside_the_set_is_refused(self):
        with pytest.raises(ValidationError, match="reason"):
            FailureClassScreeningSet.model_validate(
                {"screenings": [{"failure_mode": "fm-confabulation", "credible": True}]}
            )


class TestFailureAnalysisEntry:
    def _entry(self, **over) -> dict:
        e = {
            "failure_mode": "fm-silent-incompetence",
            "appearance": "Studies from a changed site are never scored; the "
            "worklist shows no flag.",
        }
        e.update(over)
        return e

    def test_minimal_entry(self):
        e = FailureAnalysisEntry.model_validate(self._entry())
        assert e.failed_output_distinguishable is None
        assert e.no_catching_control is False and e.no_observable is False

    def test_full_entry_round_trips(self):
        e = FailureAnalysisEntry.model_validate(
            self._entry(
                operator_view="An unflagged study in the routine queue.",
                failed_output_distinguishable=False,
                affected_person_experience="A delayed read.",
                organization_experience="A reportable event.",
                severity_rank=1,
                revised_p1="probable",
                catching_control="Daily eligible-vs-scored reconciliation per site.",
                observable="coverage ratio",
                observable_source="scoring service log",
            )
        )
        assert e.revised_p1 == "probable"
        assert FailureAnalysisEntry.model_validate(e.model_dump()) == e

    def test_none_is_a_finding_when_it_is_said(self):
        e = FailureAnalysisEntry.model_validate(
            self._entry(no_catching_control=True, no_observable=True)
        )
        assert e.catching_control is None and e.observable is None

    def test_a_flag_and_a_value_contradict(self):
        with pytest.raises(ValidationError, match="no_catching_control"):
            FailureAnalysisEntry.model_validate(
                self._entry(no_catching_control=True, catching_control="A review.")
            )
        with pytest.raises(ValidationError, match="no_observable"):
            FailureAnalysisEntry.model_validate(
                self._entry(no_observable=True, observable="coverage")
            )

    def test_a_source_needs_an_observable(self):
        with pytest.raises(ValidationError, match="observable_source"):
            FailureAnalysisEntry.model_validate(self._entry(observable_source="a log"))

    @pytest.mark.parametrize("missing", ["failure_mode", "appearance"])
    def test_required_fields(self, missing):
        data = self._entry()
        del data[missing]
        with pytest.raises(ValidationError, match=missing):
            FailureAnalysisEntry.model_validate(data)

    @pytest.mark.parametrize("bad", ["fm-omission", "fm-model-error", ""])
    def test_an_unknown_class_is_refused(self, bad):
        with pytest.raises(ValidationError, match="failure_mode"):
            FailureAnalysisEntry.model_validate(self._entry(failure_mode=bad))

    def test_rank_starts_at_one_and_p1_is_a_band(self):
        with pytest.raises(ValidationError, match="severity_rank"):
            FailureAnalysisEntry.model_validate(self._entry(severity_rank=0))
        with pytest.raises(ValidationError, match="revised_p1"):
            FailureAnalysisEntry.model_validate(self._entry(revised_p1="sometimes"))

    def test_on_the_record_the_default_is_empty(self, h01):
        assert HazardRecord.model_validate(h01).failure_analysis == []

    def test_on_the_record_it_validates_and_round_trips(self, h01):
        h01["failure_analysis"] = [
            self._entry(),
            self._entry(
                failure_mode="fm-automation-bias",
                appearance="Absence read as a negative.",
            ),
        ]
        rec = HazardRecord.model_validate(h01)
        assert [e.failure_mode for e in rec.failure_analysis] == [
            "fm-silent-incompetence",
            "fm-automation-bias",
        ]
        _round_trips(rec)

    def test_a_class_analysed_twice_on_one_record_is_refused(self, h01):
        h01["failure_analysis"] = [self._entry(), self._entry()]
        with pytest.raises(ValidationError, match="analysed twice"):
            HazardRecord.model_validate(h01)

    def test_a_bad_entry_on_the_record_is_refused(self, h01):
        h01["failure_analysis"] = [self._entry(failure_mode="fm-omission")]
        with pytest.raises(ValidationError, match="failure_analysis"):
            HazardRecord.model_validate(h01)


class TestWatchListRow:
    def test_a_complete_row_validates(self):
        r = FailureWatchListRow.model_validate(
            _row(shortfall="Queried, not connected.", item_id="S-03")
        )
        assert r.acquisition_mode == "queried"
        assert r.max_harm_level == 5
        assert FailureWatchListRow.model_validate(r.model_dump()) == r

    def test_shortfall_and_item_id_are_optional(self):
        r = FailureWatchListRow.model_validate(_row())
        assert r.shortfall is None and r.item_id is None

    def test_every_signal_access_mode_is_accepted(self):
        for mode in SignalAccess:
            FailureWatchListRow.model_validate(_row(acquisition_mode=mode.value))

    @pytest.mark.parametrize(
        "missing",
        [
            "failure_mode",
            "max_harm_level",
            "observable",
            "source",
            "acquisition_mode",
            "cadence",
            "threshold",
            "owner",
        ],
    )
    def test_required_fields(self, missing):
        data = _row()
        del data[missing]
        with pytest.raises(ValidationError, match=missing):
            FailureWatchListRow.model_validate(data)

    @pytest.mark.parametrize(
        ("field", "bad"),
        [
            ("failure_mode", "fm-omission"),
            ("acquisition_mode", "telepathy"),
            ("acquisition_mode", "sig-connected"),  # the local name, not the notation
            ("max_harm_level", 6),
            ("max_harm_level", 0),
            ("owner", ""),
            ("shortfall", ""),
        ],
    )
    def test_invalid_shapes_are_refused(self, field, bad):
        with pytest.raises(ValidationError, match=field):
            FailureWatchListRow.model_validate(_row(**{field: bad}))


class TestWatchedItemsAcceptBothForms:
    def test_bare_ids_still_validate(self, h01, h07):
        for data, ids in (
            (h01, ["S-01", "S-02"]),
            (h07, ["S-11", "S-12", "S-13", "S-14"]),
        ):
            rec = HazardRecord.model_validate(data)
            assert rec.watched_items == ids
            assert rec.watched_item_ids == ids

    def test_typed_rows_validate(self, h01):
        h01["watched_items"] = [_row(), _row(failure_mode="fm-automation-bias")]
        rec = HazardRecord.model_validate(h01)
        assert all(isinstance(w, FailureWatchListRow) for w in rec.watched_items)
        assert len(rec.watch_list_rows) == 2
        _round_trips(rec)

    def test_a_mixed_list_keeps_both_forms_in_order_without_loss(self, h01):
        h01["watched_items"] = [
            "S-01",
            _row(item_id="S-02"),
            "S-09",
            _row(shortfall="Observed only."),
        ]
        rec = HazardRecord.model_validate(h01)
        kinds = [type(w).__name__ for w in rec.watched_items]
        assert kinds == ["str", "FailureWatchListRow", "str", "FailureWatchListRow"]
        assert rec.watched_item_ids == ["S-01", "S-02", "S-09"]
        assert [r.shortfall for r in rec.watch_list_rows] == [None, "Observed only."]
        # Python and JSON round trips preserve the list exactly: bare ids stay
        # bare, rows stay rows, order and every row field survive.
        _round_trips(rec)
        dumped = json.loads(rec.model_dump_json())["watched_items"]
        assert dumped[0] == "S-01" and dumped[2] == "S-09"
        assert (
            dumped[1]["item_id"] == "S-02"
            and dumped[3]["shortfall"] == "Observed only."
        )
        assert (
            HazardRecord.model_validate_json(rec.model_dump_json()).watched_items
            == rec.watched_items
        )

    def test_model_instances_are_accepted_as_rows(self, h01):
        h01["watched_items"] = [FailureWatchListRow.model_validate(_row())]
        assert len(HazardRecord.model_validate(h01).watch_list_rows) == 1

    def test_something_that_is_neither_is_refused(self, h01):
        for bad in (
            7,
            None,
            {"observable": "only this"},
            _row(acquisition_mode="telepathy"),
        ):
            h01["watched_items"] = ["S-01", bad]
            with pytest.raises(ValidationError, match="watched_items"):
                HazardRecord.model_validate(h01)

    def test_a_typed_row_satisfies_the_tolerable_rule(self, h07):
        # Existing rule: tolerable-with-monitoring is not accepted until
        # watched_items names something. A typed row names something.
        h07["watched_items"] = []
        with pytest.raises(ValidationError, match="watched_items is empty"):
            HazardRecord.model_validate(h07)
        h07["watched_items"] = [_row()]
        HazardRecord.model_validate(h07)

    def test_the_json_schema_describes_both_forms(self):
        items = HazardRecord.model_json_schema()["properties"]["watched_items"]["items"]
        kinds = {tuple(sorted(branch)) for branch in items["anyOf"]}
        assert ("type",) in kinds and ("$ref",) in kinds


class TestNotAdded:
    """Deferred on purpose (ASHFORGE-827); a test keeps the line visible."""

    def test_p2_is_one_per_record_and_the_dimensions_are_four(self):
        assert set(HarmAssessment.model_fields) == {
            "patient",
            "staff",
            "economic",
            "reputational",
        }
        assert set(DimensionHarm.model_fields) == {
            "level",
            "rationale",
            "not_reachable",
            "not_reachable_reason",
        }
        from ashmatics_datamodels.risk import ProbabilityPosition

        assert set(ProbabilityPosition.model_fields) == {"p1", "p2"}

    def test_reanalysis_triggers_stay_free_text(self, h01):
        h01["reanalysis_triggers"] = [{"type": "model_change", "threshold": "any"}]
        with pytest.raises(ValidationError, match="reanalysis_triggers"):
            HazardRecord.model_validate(h01)
