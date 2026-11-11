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

"""0.26.0 (ASHFORGE-942): a control's id, kind, implementation and the ASHC
controls it serves. All optional, so a record written before validates."""

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.risk import ControlKind, HazardRecord, RiskControl

BASE = {
    "description": "A second reader checks every scan the model scores low",
    "tier": "protective_measure",
    "reduces": "p2",
    "owner": "Neuroradiology section lead",
}


class TestOlderControlsStillValidate:
    def test_a_control_without_the_new_fields(self):
        control = RiskControl.model_validate(BASE)
        assert control.control_id is None
        assert control.kind is None
        assert control.implemented is None
        assert control.serves_controls == []

    def test_the_worked_records_still_validate(self, h01, h07):
        for data in (h01, h07):
            rec = HazardRecord.model_validate(data)
            assert HazardRecord.model_validate(rec.model_dump()) == rec


class TestTheNewFields:
    def test_all_of_them_round_trip(self):
        control = RiskControl.model_validate({
            **BASE,
            "control_id": "c-7f3a",
            "kind": "organizational_human",
            "implemented": {"reference": "Rota updated", "dated": "2026-11-05"},
            "verification": {"reference": "Audit of 50 scans", "dated": "2026-11-09"},
            "serves_controls": ["ASHC-OPS-02", "ASHC-RM-01"],
        })
        assert control.kind == ControlKind.ORGANIZATIONAL_HUMAN.value
        assert RiskControl.model_validate(control.model_dump()) == control

    def test_the_two_kinds(self):
        assert {k.value for k in ControlKind} == {"technical", "organizational_human"}
        with pytest.raises(ValidationError):
            RiskControl.model_validate({**BASE, "kind": "vendor"})

    @pytest.mark.parametrize("bad", ["", "has space", "-leading", "x" * 65])
    def test_a_control_id_is_a_plain_token(self, bad):
        with pytest.raises(ValidationError):
            RiskControl.model_validate({**BASE, "control_id": bad})

    @pytest.mark.parametrize("bad", ["ASHC-OPS-2", "ashc-ops-02", "OPS-02", "ASHC-OPS-02x"])
    def test_serves_controls_takes_ashc_ids_only(self, bad):
        with pytest.raises(ValidationError):
            RiskControl.model_validate({**BASE, "serves_controls": ["ASHC-RM-01", bad]})

    def test_an_ashc_control_is_named_once(self):
        with pytest.raises(ValidationError, match="named once"):
            RiskControl.model_validate({**BASE, "serves_controls": ["ASHC-OPS-02", "ASHC-OPS-02"]})

    def test_verification_is_not_dated_before_implementation(self):
        with pytest.raises(ValidationError, match="precedes implementation"):
            RiskControl.model_validate({
                **BASE,
                "implemented": {"reference": "Rota updated", "dated": "2026-11-09"},
                "verification": {"reference": "Audit", "dated": "2026-11-05"},
            })

    def test_verified_without_an_implemented_record_is_allowed(self):
        """A control checked in place before anyone recorded putting it
        there (every control written before 0.26.0) is Verified."""
        control = RiskControl.model_validate({
            **BASE, "verification": {"reference": "Audit", "dated": "2026-11-05"},
        })
        assert control.implemented is None
