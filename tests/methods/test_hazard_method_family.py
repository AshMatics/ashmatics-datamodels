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
The hazard analysis method family in the contract (ASHFORGE-828; coreapp
ADR-061 D2; aigov-framework ``method_registry.yaml`` v0.3.0, CLF v0.11.0).

What 0.22.0 adds, each with present / absent / invalid cases:

- ``MethodFamily.HAZARD_ANALYSIS``
- ``MethodDefinition.depth_applicability`` (``DepthApplicability``)
- ``MethodDefinition.forbidden_decisions`` (``ForbiddenDecision``)
- ``ConditionScope.RECORD`` and ``RecordAttribute``

The last class loads the framework's actual ``method_registry.yaml`` and
``process-domain-registry.json`` through the contract. The framework is
found the way the other live tests find it: ``ASHMATICS_AIGOV_FRAMEWORK_DIR``,
then a sibling checkout, else those tests skip.
"""

import json
import os
import re
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.methods import (
    ConditionScope,
    DepthApplicability,
    ForbiddenDecision,
    MethodDefinition,
    MethodFamily,
    MethodRegistry,
    RecordAttribute,
    SystemAttribute,
)
from ashmatics_datamodels.risk import HarmLevel, LinkType, analysis_depth

FOUR_DECISIONS = [
    "define_scales",
    "score_harm",
    "decide_gate",
    "design_bias_mitigation",
]

# A method as it was before 0.22.0: neither new field.
LEGACY_METHOD = {
    "method_id": "mth://fairness.subgroup_auroc",
    "label": "Subgroup AUROC comparison",
    "family": "group_fairness",
    "description": "Compare discrimination across strata.",
    "junction_refs": ["SOP-EF-01.S1"],
    "executable_by": ["{{tool.biasAssess}}"],
    "phase": "both",
    "applicability": {"ai_paradigm": ["ap-predictive"]},
    "evidence_basis": [{"type": "doi", "ref": "10.1126/science.aax2342"}],
    "default_for": [{"condition": "{{system.riskTier}} == 'high'", "rank": 1}],
    "review": {"last_reviewed": date(2026, 10, 11)},
}

HAZARD_METHOD = {
    "method_id": "mth://hazard.stpa",
    "label": "System-theoretic process analysis (STPA)",
    "family": "hazard_analysis",
    "description": "Control structure, unsafe control actions, loss scenarios.",
    "junction_refs": ["SOP-RM-01.S5", "SOP-RM-02.S3"],
    "phase": "both",
    "applicability": {"ai_paradigm": ["ap-predictive", "ap-agentic"]},
    "evidence_basis": [{"type": "ref", "ref": "PMC13421477"}],
    "default_for": [
        {
            "condition": "{{record.sequenceStructure}}.includes('multiple_controllers')",
            "rank": 1,
        }
    ],
    "depth_applicability": {
        "mandatory_at_harm_levels": [4, 5],
        "harm_model_tier": "full_safety_analysis",
    },
    "forbidden_decisions": FOUR_DECISIONS,
    "review": {"last_reviewed": date(2026, 10, 11)},
}


class TestHazardAnalysisFamily:
    def test_present(self):
        assert MethodFamily.HAZARD_ANALYSIS.value == "hazard_analysis"
        m = MethodDefinition.model_validate(HAZARD_METHOD)
        assert m.family == "hazard_analysis"  # use_enum_values

    def test_the_other_six_families_are_unchanged(self):
        assert {f.value for f in MethodFamily} == {
            "group_fairness",
            "individual_fairness",
            "bias_mitigation",
            "validation_statistics",
            "drift_detection",
            "explainability",
            "hazard_analysis",
        }

    @pytest.mark.parametrize(
        "family", ["hazard-analysis", "hazard", "Hazard_Analysis", ""]
    )
    def test_invalid_spellings_are_refused(self, family):
        with pytest.raises(ValidationError, match="family"):
            MethodDefinition.model_validate({**HAZARD_METHOD, "family": family})


class TestDepthApplicability:
    def test_present_and_mandatory(self):
        d = DepthApplicability.model_validate(
            {
                "mandatory_at_harm_levels": [4, 5],
                "harm_model_tier": "full_safety_analysis",
            }
        )
        assert d.mandatory_at_harm_levels == [4, 5]
        assert d.harm_model_tier == "full_safety_analysis"

    def test_present_and_mandatory_nowhere(self):
        """The shape PHA, use-case scenarios, FMEA and HAZOP carry."""
        d = DepthApplicability.model_validate({"mandatory_at_harm_levels": []})
        assert d.mandatory_at_harm_levels == []
        assert d.harm_model_tier is None

    def test_the_list_defaults_empty(self):
        assert DepthApplicability.model_validate({}).mandatory_at_harm_levels == []

    def test_absent_on_a_method_leaves_every_old_entry_valid(self):
        m = MethodDefinition.model_validate(LEGACY_METHOD)
        assert m.depth_applicability is None
        assert "depth_applicability" not in m.model_dump(exclude_none=True)

    def test_present_on_a_method_round_trips(self):
        m = MethodDefinition.model_validate(HAZARD_METHOD)
        assert m.depth_applicability is not None
        assert m.depth_applicability.mandatory_at_harm_levels == [4, 5]
        assert m.model_dump(exclude_none=True)["depth_applicability"] == {
            "mandatory_at_harm_levels": [4, 5],
            "harm_model_tier": "full_safety_analysis",
        }

    @pytest.mark.parametrize("levels", [[0], [6], [-1], [4, 6], [3.5], ["high"], 4])
    def test_levels_outside_the_scale_or_not_a_list_of_ints_are_refused(self, levels):
        with pytest.raises(ValidationError, match="mandatory_at_harm_levels"):
            DepthApplicability.model_validate(
                {
                    "mandatory_at_harm_levels": levels,
                    "harm_model_tier": "full_safety_analysis",
                }
            )

    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
    def test_every_harm_level_is_accepted(self, level):
        d = DepthApplicability.model_validate(
            {"mandatory_at_harm_levels": [level], "harm_model_tier": "t"}
        )
        assert d.mandatory_at_harm_levels == [level]

    def test_a_tier_is_required_when_the_list_is_not_empty(self):
        with pytest.raises(ValidationError, match="harm_model_tier is required"):
            DepthApplicability.model_validate({"mandatory_at_harm_levels": [4, 5]})

    def test_an_empty_tier_does_not_satisfy_the_requirement(self):
        with pytest.raises(ValidationError, match="harm_model_tier"):
            DepthApplicability.model_validate(
                {"mandatory_at_harm_levels": [4], "harm_model_tier": ""}
            )

    def test_an_unknown_key_is_refused(self):
        with pytest.raises(ValidationError, match="mandatory_at_harm_level"):
            DepthApplicability.model_validate({"mandatory_at_harm_level": [4]})

    def test_invalid_through_the_method(self):
        bad = {
            **HAZARD_METHOD,
            "depth_applicability": {"mandatory_at_harm_levels": [9]},
        }
        with pytest.raises(ValidationError, match="depth_applicability"):
            MethodDefinition.model_validate(bad)


class TestForbiddenDecisions:
    def test_the_closed_list_is_the_four(self):
        assert [m.value for m in ForbiddenDecision] == FOUR_DECISIONS

    def test_present(self):
        m = MethodDefinition.model_validate(HAZARD_METHOD)
        assert m.forbidden_decisions == FOUR_DECISIONS  # use_enum_values

    @pytest.mark.parametrize("decision", FOUR_DECISIONS)
    def test_each_decision_is_accepted_alone(self, decision):
        m = MethodDefinition.model_validate(
            {**HAZARD_METHOD, "forbidden_decisions": [decision]}
        )
        assert m.forbidden_decisions == [decision]

    def test_absent_leaves_every_old_entry_valid(self):
        m = MethodDefinition.model_validate(LEGACY_METHOD)
        assert m.forbidden_decisions is None
        assert "forbidden_decisions" not in m.model_dump(exclude_none=True)

    def test_an_empty_list_is_a_statement_not_an_absence(self):
        """Whether a family requires the field is the framework's check; the
        contract only keeps absent and empty apart."""
        m = MethodDefinition.model_validate(
            {**HAZARD_METHOD, "forbidden_decisions": []}
        )
        assert m.forbidden_decisions == []

    @pytest.mark.parametrize("bad", ["approve_gate", "score-harm", "", "DECIDE_GATE"])
    def test_a_decision_outside_the_closed_list_is_refused(self, bad):
        with pytest.raises(ValidationError, match="forbidden_decisions"):
            MethodDefinition.model_validate(
                {**HAZARD_METHOD, "forbidden_decisions": [bad]}
            )

    def test_a_repeat_is_refused(self):
        with pytest.raises(ValidationError, match="must not repeat"):
            MethodDefinition.model_validate(
                {**HAZARD_METHOD, "forbidden_decisions": ["score_harm", "score_harm"]}
            )

    def test_a_bare_string_is_not_a_list(self):
        with pytest.raises(ValidationError, match="forbidden_decisions"):
            MethodDefinition.model_validate(
                {**HAZARD_METHOD, "forbidden_decisions": "score_harm"}
            )


RECORD_ATTRIBUTES = {
    "record.harmLevel": {
        "type": "integer",
        "source": "hazard_record",
        "allowed_values": [1, 2, 3, 4, 5],
        "note": "The harm level of this hazard record.",
    },
    "record.linkTypes": {
        "type": "array",
        "source": "hazard_record",
        "allowed_values": ["technical", "human", "organizational"],
    },
    "record.sequenceStructure": {
        "type": "array",
        "source": "analyst_judgement",
        "allowed_values": [
            "multiple_controllers",
            "delayed_feedback",
            "human_ai_interaction",
            "defined_top_event",
            "stepwise_workflow",
            "component_enumeration",
        ],
    },
}


class TestRecordScope:
    def test_the_scope_exists(self):
        assert ConditionScope.RECORD.value == "record"
        assert {s.value for s in ConditionScope} == {"org", "system", "record"}

    @pytest.mark.parametrize("name", list(RECORD_ATTRIBUTES))
    def test_each_registered_attribute_validates(self, name):
        a = RecordAttribute.model_validate({"name": name, **RECORD_ATTRIBUTES[name]})
        assert a.name == name

    def test_the_two_sources(self):
        judged = RecordAttribute.model_validate(
            {
                "name": "record.sequenceStructure",
                **RECORD_ATTRIBUTES["record.sequenceStructure"],
            }
        )
        stored = RecordAttribute.model_validate(
            {"name": "record.harmLevel", **RECORD_ATTRIBUTES["record.harmLevel"]}
        )
        assert (judged.source, stored.source) == ("analyst_judgement", "hazard_record")

    def test_a_source_is_required(self):
        """Stored and judged are told apart by the source, so it cannot be absent."""
        spec = {
            k: v
            for k, v in RECORD_ATTRIBUTES["record.harmLevel"].items()
            if k != "source"
        }
        with pytest.raises(ValidationError, match="source"):
            RecordAttribute.model_validate({"name": "record.harmLevel", **spec})

    @pytest.mark.parametrize(
        "source", ["ai_inventory", "risk_register", "triage_record", "judgement", ""]
    )
    def test_a_source_outside_the_two_is_refused(self, source):
        spec = {**RECORD_ATTRIBUTES["record.harmLevel"], "source": source}
        with pytest.raises(ValidationError, match="source"):
            RecordAttribute.model_validate({"name": "record.harmLevel", **spec})

    @pytest.mark.parametrize(
        "name",
        [
            "system.harmLevel",
            "org.harmLevel",
            "harmLevel",
            "record",
            "record.",
            "record.HarmLevel",
        ],
    )
    def test_a_name_must_be_record_scoped(self, name):
        with pytest.raises(ValidationError, match="name"):
            RecordAttribute.model_validate(
                {"name": name, **RECORD_ATTRIBUTES["record.harmLevel"]}
            )

    def test_an_unknown_key_is_refused(self):
        spec = {
            **RECORD_ATTRIBUTES["record.harmLevel"],
            "skos_scheme": "ash:AIParadigmScheme",
        }
        with pytest.raises(ValidationError, match="skos_scheme"):
            RecordAttribute.model_validate({"name": "record.harmLevel", **spec})

    def test_the_system_scope_stays_closed_to_record_values(self):
        """Accepting record sources and names on SystemAttribute would loosen it."""
        with pytest.raises(ValidationError, match="source"):
            SystemAttribute.model_validate(
                {
                    "name": "system.harmLevel",
                    "type": "integer",
                    "source": "hazard_record",
                }
            )
        with pytest.raises(ValidationError, match="name"):
            SystemAttribute.model_validate(
                {"name": "record.harmLevel", "type": "integer"}
            )


# ---------------------------------------------------------------------------
# The framework's actual files, through the contract.
# ---------------------------------------------------------------------------


def _framework_dir() -> Path | None:
    env = os.environ.get("ASHMATICS_AIGOV_FRAMEWORK_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    sibling = Path(__file__).resolve().parents[2].parent / "ashmatics-aigov-framework"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="module")
def framework() -> Path:
    d = _framework_dir()
    if d is None:
        pytest.skip(
            "aigov-framework checkout not found; set ASHMATICS_AIGOV_FRAMEWORK_DIR"
        )
    return d


@pytest.fixture(scope="module")
def registry(framework) -> MethodRegistry:
    yaml = pytest.importorskip("yaml")
    path = framework / "method_registry.yaml"
    if not path.is_file():
        pytest.skip(f"no method_registry.yaml in {framework}")
    return MethodRegistry.model_validate(yaml.safe_load(path.read_text()))


@pytest.fixture(scope="module")
def condition_scopes(framework) -> dict:
    path = framework / "process-domain-registry.json"
    if not path.is_file():
        pytest.skip(f"no process-domain-registry.json in {framework}")
    return json.loads(path.read_text())["conditional_logic_framework"][
        "rule_engine_schema"
    ]["condition_scopes"]


class TestFrameworkRegistryThroughTheContract:
    def test_the_whole_method_registry_validates(self, registry):
        # Floors, not equalities: the registry grows. 28 methods and 7 sets
        # is v0.3.0, the first with the hazard analysis family.
        assert len(registry.methods) >= 28
        assert len(registry.method_sets) >= 7

    def test_the_hazard_family_is_six_methods_with_both_fields(self, registry):
        family = [m for m in registry.methods if m.family == "hazard_analysis"]
        assert {m.method_id for m in family} == {
            "mth://hazard.pha",
            "mth://hazard.use_case_scenarios",
            "mth://hazard.fmea",
            "mth://hazard.fta",
            "mth://hazard.hazop",
            "mth://hazard.stpa",
        }
        for m in family:
            assert m.depth_applicability is not None, m.method_id
            assert m.forbidden_decisions == FOUR_DECISIONS, m.method_id
            assert set(m.applicability.ai_paradigm or []) == {
                "ap-predictive",
                "ap-forecasting",
                "ap-generative",
                "ap-agentic",
                "ap-hybrid",
                "ap-neurosymbolic",
                "ap-rule-based",
                "ap-causal",
            }, m.method_id

    def test_the_set_holds_the_family(self, registry):
        family = {
            m.method_id for m in registry.methods if m.family == "hazard_analysis"
        }
        core = next(s for s in registry.method_sets if s.set_id == "mset://hazard.core")
        for phase in ("validation", "operational"):
            assert set(core.members[phase]) == family

    def test_methods_outside_the_family_carry_neither_field(self, registry):
        for m in registry.methods:
            if m.family != "hazard_analysis":
                assert m.depth_applicability is None, m.method_id
                assert m.forbidden_decisions is None, m.method_id

    def test_mandatory_levels_are_the_levels_the_tier_earns(self, registry):
        """The registry's rule agrees with the contract's own derivation
        (``risk.analysis_depth``), not only with harm_model.yaml."""
        mandatory_at: dict[int, list[str]] = {}
        for m in registry.methods:
            d = m.depth_applicability
            if d is None:
                continue
            if d.mandatory_at_harm_levels:
                earned = {
                    int(lv)
                    for lv in HarmLevel
                    if analysis_depth(lv).value == d.harm_model_tier
                }
                assert set(d.mandatory_at_harm_levels) == earned, m.method_id
            for lv in d.mandatory_at_harm_levels:
                mandatory_at.setdefault(lv, []).append(m.method_id)
        # The full safety analysis levels each name at least one method, so a
        # record there always has a method it may choose.
        for lv in (4, 5):
            assert mandatory_at.get(lv), (
                f"no hazard method is mandatory at harm level {lv}"
            )

    def test_conditions_read_only_registered_record_tokens(
        self, registry, condition_scopes
    ):
        registered = set(condition_scopes["record"]["registered_attributes"])
        token = re.compile(r"\{\{((?:system|record)\.\w+)\}\}")
        for m in registry.methods:
            if m.family != "hazard_analysis":
                continue
            for rule in m.default_for:
                for tok in token.findall(rule.condition):
                    assert tok in registered, f"{m.method_id}: {tok}"


class TestFrameworkConditionScopesThroughTheContract:
    def test_every_scope_is_a_condition_scope(self, condition_scopes):
        assert set(condition_scopes) == {s.value for s in ConditionScope}

    def test_every_system_attribute_validates(self, condition_scopes):
        attrs = condition_scopes["system"]["registered_attributes"]
        assert attrs
        for name, spec in attrs.items():
            SystemAttribute.model_validate({"name": name, **spec})

    def test_every_record_attribute_validates(self, condition_scopes):
        attrs = condition_scopes["record"]["registered_attributes"]
        assert set(attrs) == set(RECORD_ATTRIBUTES)
        for name, spec in attrs.items():
            RecordAttribute.model_validate({"name": name, **spec})

    def test_stored_and_judged_are_told_apart(self, condition_scopes):
        attrs = condition_scopes["record"]["registered_attributes"]
        assert attrs["record.harmLevel"]["source"] == "hazard_record"
        assert attrs["record.linkTypes"]["source"] == "hazard_record"
        assert attrs["record.sequenceStructure"]["source"] == "analyst_judgement"

    def test_stored_values_match_the_enums_they_are_read_from(self, condition_scopes):
        attrs = condition_scopes["record"]["registered_attributes"]
        assert attrs["record.harmLevel"]["allowed_values"] == [
            m.value for m in HarmLevel
        ]
        assert set(attrs["record.linkTypes"]["allowed_values"]) == {
            m.value for m in LinkType
        }
