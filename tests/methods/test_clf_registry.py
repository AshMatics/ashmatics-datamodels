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
``SystemAttribute`` against the CLF system attributes the aigov-framework
actually registers, and the ADR-031 attributes against their enums.

Until 0.16.0 the contract could not hold the registry it describes: it had no
``integer`` type (``system.harmLevel``), no ``allowed_values`` (eleven of
fourteen attributes carry one), and no ``deprecated`` / ``superseded_by``
(``system.patientFacing``). Nothing validated the registry through it, so the
drift was invisible. This test is that validation. It reads the sibling
checkout, or ``ASHMATICS_AIGOV_FRAMEWORK_DIR``, and skips without one.
"""

import json
import os
from pathlib import Path

import pytest

from ashmatics_datamodels.common.enums import SignalAccess
from ashmatics_datamodels.methods import SystemAttribute
from ashmatics_datamodels.registry import RegistrySourcing, SolutionShape
from ashmatics_datamodels.risk import HarmLevel, RiskTier


def _framework_dir() -> Path | None:
    env = os.environ.get("ASHMATICS_AIGOV_FRAMEWORK_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    sibling = Path(__file__).resolve().parents[2].parent / "ashmatics-aigov-framework"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="module")
def registered() -> dict[str, dict]:
    d = _framework_dir()
    if d is None:
        pytest.skip("aigov-framework checkout not found; set ASHMATICS_AIGOV_FRAMEWORK_DIR")
    reg = json.loads((d / "process-domain-registry.json").read_text())
    attrs = reg["conditional_logic_framework"]["rule_engine_schema"]["condition_scopes"][
        "system"
    ]["registered_attributes"]
    assert attrs, "no registered system attributes found"
    return attrs


def test_every_registered_attribute_validates(registered):
    for name, spec in registered.items():
        SystemAttribute.model_validate({"name": name, **spec})


def test_harm_level_matches_the_enum(registered):
    spec = registered["system.harmLevel"]
    assert spec["type"] == "integer"
    assert spec["allowed_values"] == [m.value for m in HarmLevel]


def test_signal_access_matches_the_enum(registered):
    spec = registered["system.signalAccess"]
    assert (spec["type"], spec["skos_scheme"]) == ("array", "ash:SignalAccessScheme")
    assert set(spec["allowed_values"]) == {m.value for m in SignalAccess}


def test_risk_tier_matches_the_enum(registered):
    assert set(registered["system.riskTier"]["allowed_values"]) == {m.value for m in RiskTier}


def test_sourcing_matches_the_derived_triad(registered):
    """system.sourcing is registry.derive.sourcing_obligation's output."""
    spec = registered["system.sourcing"]
    assert set(spec["allowed_values"]) == {m.value for m in RegistrySourcing}
    assert "skos_scheme" not in spec  # derived product vocabulary, no scheme


def test_solution_shape_matches_the_enum(registered):
    """system.solutionShape is CHAR product vocabulary, carried inline like sourcing."""
    spec = registered["system.solutionShape"]
    assert set(spec["allowed_values"]) == {m.value for m in SolutionShape}
    assert "skos_scheme" not in spec


def test_superseded_by_requires_deprecated():
    with pytest.raises(ValueError, match="not marked deprecated"):
        SystemAttribute.model_validate(
            {"name": "system.patientFacing", "type": "boolean", "superseded_by": "system.affectsPersons"}
        )


def test_pre_registration_source_requires_a_source():
    """
    An attribute intake can screen on must also resolve after registration.
    pre_registration_source says where the value comes from in the gap, not
    instead of the operational store (ADR-033 D4).
    """
    with pytest.raises(ValueError, match="resolves nowhere"):
        SystemAttribute.model_validate(
            {
                "name": "system.affectsPersons",
                "type": "boolean",
                "pre_registration_source": "triage_record",
            }
        )


def test_pre_registration_source_accepted_alongside_a_source():
    spec = SystemAttribute.model_validate(
        {
            "name": "system.affectsPersons",
            "type": "boolean",
            "source": "ai_inventory",
            "pre_registration_source": "triage_record",
        }
    )
    assert spec.pre_registration_source == "triage_record"


def test_a_scheme_typed_attribute_may_screen_at_intake():
    """
    system.aiParadigm names no store: skos_scheme alone defines its value
    space, and it resolves from the inventory's ontology tagging. It is
    still screenable at intake, so the constraint reads skos_scheme as a
    resolution path too.
    """
    spec = SystemAttribute.model_validate(
        {
            "name": "system.aiParadigm",
            "type": "string",
            "skos_scheme": "ash:AIParadigmScheme",
            "pre_registration_source": "triage_record",
        }
    )
    assert spec.source is None
    assert spec.pre_registration_source == "triage_record"


def test_triage_record_is_the_only_pre_registration_source():
    """The Triage Record is the one thing that exists before registration."""
    with pytest.raises(ValueError):
        SystemAttribute.model_validate(
            {
                "name": "system.riskTier",
                "type": "string",
                "source": "risk_register",
                "pre_registration_source": "ai_inventory",
            }
        )
