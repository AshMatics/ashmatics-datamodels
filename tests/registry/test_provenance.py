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

"""Provenance on registered attribute values (aigov-framework ADR-033 D4)."""

from datetime import datetime

import pytest

from ashmatics_datamodels.registry import (
    AttributeValueSource,
    RegisteredAttributeValue,
    current_value,
    differs_from_triage,
)

T0 = datetime(2026, 9, 14, 9, 0)
T1 = datetime(2026, 9, 20, 14, 0)
T2 = datetime(2026, 9, 21, 10, 0)


def screened(value, value_id="v1", attribute="system.actionAuthority"):
    return RegisteredAttributeValue(
        value_id=value_id, attribute=attribute, value=value,
        source=AttributeValueSource.TRIAGE_RECORD, source_record_id="TR-0042",
        recorded_by="intake coordinator", recorded_at=T0,
    )


def corrected(value, supersedes, value_id="v2", at=T1, attribute="system.actionAuthority"):
    return RegisteredAttributeValue(
        value_id=value_id, attribute=attribute, value=value,
        source=AttributeValueSource.RISK_REGISTER, source_record_id="HAR-0007",
        recorded_by="risk manager", recorded_at=at, supersedes=supersedes,
    )


def test_a_screened_value_must_name_its_triage_record():
    with pytest.raises(ValueError, match="must name the Triage Record"):
        RegisteredAttributeValue(
            value_id="v1", attribute="system.affectsPersons", value=True,
            source=AttributeValueSource.TRIAGE_RECORD,
            recorded_by="intake coordinator", recorded_at=T0,
        )


def test_a_value_cannot_supersede_itself():
    with pytest.raises(ValueError, match="cannot supersede itself"):
        corrected("act_with_approval", supersedes="v2", value_id="v2")


def test_the_screened_value_is_in_force_until_corrected():
    history = [screened("recommend_only")]
    assert current_value(history, "system.actionAuthority").value == "recommend_only"
    assert differs_from_triage(history, "system.actionAuthority") is False


def test_a_correction_supersedes_and_flips():
    history = [screened("recommend_only"), corrected("act_with_approval", supersedes="v1")]
    assert current_value(history, "system.actionAuthority").value_id == "v2"
    assert differs_from_triage(history, "system.actionAuthority") is True


def test_a_confirmation_that_repeats_the_screen_does_not_flip():
    history = [screened("recommend_only"), corrected("recommend_only", supersedes="v1")]
    assert differs_from_triage(history, "system.actionAuthority") is False


def test_a_correction_undone_later_does_not_flip():
    history = [
        screened("recommend_only"),
        corrected("act_with_approval", supersedes="v1"),
        corrected("recommend_only", supersedes="v2", value_id="v3", at=T2),
    ]
    assert current_value(history, "system.actionAuthority").value_id == "v3"
    assert differs_from_triage(history, "system.actionAuthority") is False


def test_two_values_in_force_is_a_defect_not_a_tie():
    history = [screened("recommend_only"), corrected("act_autonomously", supersedes=None)]
    with pytest.raises(ValueError, match="more than one value in force"):
        current_value(history, "system.actionAuthority")


def test_an_attribute_triage_never_screened_cannot_flip():
    history = [corrected(3, supersedes=None, value_id="h1", attribute="system.harmLevel")]
    assert differs_from_triage(history, "system.harmLevel") is False
    assert current_value(history, "system.actionAuthority") is None


def test_attributes_do_not_leak_into_each_other():
    history = [
        screened("recommend_only"),
        screened(True, value_id="p1", attribute="system.affectsPersons"),
        corrected(False, supersedes="p1", value_id="p2", attribute="system.affectsPersons"),
    ]
    assert differs_from_triage(history, "system.actionAuthority") is False
    assert differs_from_triage(history, "system.affectsPersons") is True
