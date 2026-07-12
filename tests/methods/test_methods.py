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
Method-contract validation tests, including the ASHKBAPP-99 acceptance
round-trip: the live aigov-framework method_registry.yaml must parse ->
validate -> serialize without loss.

Registry source resolution mirrors the ontology guard's convention:
``ASHMATICS_AIGOV_FRAMEWORK_DIR`` env var, then a checkout of
``ashmatics-aigov-framework`` beside this repo, else the round-trip test
skips (unit tests below run regardless).
"""

import os
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.methods import (
    ApplicabilityProfile,
    ApprovedMethodSet,
    MethodDefinition,
    MethodRegistry,
    MethodSet,
    SystemAttribute,
)


def _registry_path() -> Path | None:
    env = os.environ.get("ASHMATICS_AIGOV_FRAMEWORK_DIR")
    if env:
        p = Path(env).expanduser() / "method_registry.yaml"
        return p if p.is_file() else None
    repo_root = Path(__file__).resolve().parents[2]
    sibling = repo_root.parent / "ashmatics-aigov-framework" / "method_registry.yaml"
    return sibling if sibling.is_file() else None


VALID_METHOD = {
    "method_id": "mth://fairness.subgroup_auroc",
    "label": "Subgroup AUROC comparison",
    "family": "group_fairness",
    "description": "Compare discrimination across strata.",
    "junction_refs": ["SOP-EF-01.S1"],
    "executable_by": ["tool://bias.assess"],
    "phase": "both",
    "applicability": {
        "ai_paradigm": ["ap-predictive"],
        "fairness_factors": ["ff-age", "ff-sex"],
        "min_subgroup_n": 100,
    },
    "evidence_basis": [
        {"type": "doi", "ref": "10.1126/science.aax2342", "note": "Obermeyer 2019"}
    ],
    "default_for": [
        {"condition": "{{system.riskTier}} == 'high'", "rank": 1}
    ],
    "review": {"last_reviewed": date(2026, 7, 11)},
}


class TestMethodDefinition:
    def test_valid_method_parses(self):
        m = MethodDefinition.model_validate(VALID_METHOD)
        assert m.method_id == "mth://fairness.subgroup_auroc"
        assert m.family == "group_fairness"  # use_enum_values

    def test_malformed_method_id_rejected(self):
        bad = {**VALID_METHOD, "method_id": "fairness.subgroup_auroc"}
        with pytest.raises(ValidationError, match="method_id"):
            MethodDefinition.model_validate(bad)

    def test_free_string_applicability_rejected(self):
        """ADR-011's zero-free-string criterion, now contract-enforced."""
        bad = {
            **VALID_METHOD,
            "applicability": {"ai_paradigm": ["deep learning"]},
        }
        with pytest.raises(ValidationError, match="ai_paradigm"):
            MethodDefinition.model_validate(bad)

    def test_empty_evidence_basis_rejected(self):
        bad = {**VALID_METHOD, "evidence_basis": []}
        with pytest.raises(ValidationError, match="evidence_basis"):
            MethodDefinition.model_validate(bad)

    def test_malformed_junction_ref_rejected(self):
        bad = {**VALID_METHOD, "junction_refs": ["SOP-EF-1.S1"]}
        with pytest.raises(ValidationError, match="junction_refs"):
            MethodDefinition.model_validate(bad)

    def test_unknown_applicability_axis_rejected(self):
        """extra='forbid' closes the unknown-axis hole the old validator
        checked by hand."""
        bad = {
            **VALID_METHOD,
            "applicability": {"clinical_domain": ["radiology"]},
        }
        with pytest.raises(ValidationError):
            MethodDefinition.model_validate(bad)


class TestApplicabilityProfile:
    def test_model_class_axis_accepts_scheme_concepts(self):
        p = ApplicabilityProfile.model_validate(
            {"model_class": ["mc-tree-ensemble", "mc-linear"]}
        )
        assert p.model_class == ["mc-tree-ensemble", "mc-linear"]

    def test_min_subgroup_n_must_be_positive(self):
        with pytest.raises(ValidationError, match="min_subgroup_n"):
            ApplicabilityProfile.model_validate({"min_subgroup_n": 0})


class TestMethodSet:
    VALID_SET = {
        "set_id": "mset://fairness.core",
        "label": "Core set",
        "description": "The single org-approved fairness set.",
        "serves_junctions": [
            {"ref": "SOP-EF-01.S1", "phase": "validation", "note": "primary"}
        ],
        "members": {"validation": ["mth://fairness.subgroup_auroc"]},
        "token": "{{efApprovedFairnessMethods}}",
    }

    def test_valid_set_parses(self):
        s = MethodSet.model_validate(self.VALID_SET)
        assert s.set_id == "mset://fairness.core"

    def test_both_is_not_a_member_phase_key(self):
        bad = {
            **self.VALID_SET,
            "members": {"both": ["mth://fairness.subgroup_auroc"]},
        }
        with pytest.raises(ValidationError, match="members"):
            MethodSet.model_validate(bad)

    def test_approved_set_requires_adjustment_rationale(self):
        approved = {
            **self.VALID_SET,
            "organization_id": "org-001",
            "resolved_members": {"validation": ["mth://fairness.subgroup_auroc"]},
            "delivery_mode": "align",
            "adjustments": [
                {
                    "action": "removed",
                    "method_id": "mth://fairness.demographic_parity",
                    "phase": "validation",
                    "rationale": "",
                }
            ],
        }
        with pytest.raises(ValidationError, match="rationale"):
            ApprovedMethodSet.model_validate(approved)
        approved["adjustments"][0]["rationale"] = "prevalence differs by design"
        assert ApprovedMethodSet.model_validate(approved).delivery_mode == "align"


class TestSystemAttribute:
    def test_scheme_bound_attribute(self):
        a = SystemAttribute.model_validate(
            {
                "name": "system.aiParadigm",
                "type": "string",
                "skos_scheme": "ash:AIParadigmScheme",
            }
        )
        assert a.source is None

    def test_name_must_be_system_scoped(self):
        with pytest.raises(ValidationError, match="name"):
            SystemAttribute.model_validate(
                {"name": "org.riskTier", "type": "string"}
            )


class TestRegistryCrossReferences:
    def test_set_member_must_be_defined(self):
        reg = {
            "registry_metadata": {
                "registry_id": "t",
                "version": "0.1.0",
                "status": "pilot",
                "scope": "test",
                "created": date(2026, 7, 11),
                "last_updated": date(2026, 7, 11),
                "review_cycle": "annual",
                "adr_refs": ["ADR-011"],
                "jira": "ASHKBAPP-100",
            },
            "methods": [VALID_METHOD],
            "method_sets": [
                {
                    **TestMethodSet.VALID_SET,
                    "members": {"validation": ["mth://fairness.undefined_method"]},
                }
            ],
        }
        with pytest.raises(ValidationError, match="not defined in"):
            MethodRegistry.model_validate(reg)


class TestRegistryRoundTrip:
    """ASHKBAPP-99 acceptance: the live registry round-trips without loss."""

    @pytest.fixture(scope="class")
    def registry_dict(self):
        yaml = pytest.importorskip("yaml")
        path = _registry_path()
        if path is None:
            pytest.skip(
                "method_registry.yaml not found. Set "
                "ASHMATICS_AIGOV_FRAMEWORK_DIR or check out "
                "ashmatics-aigov-framework beside this repo."
            )
        with open(path) as f:
            return yaml.safe_load(f)

    def test_registry_validates(self, registry_dict):
        reg = MethodRegistry.model_validate(registry_dict)
        assert len(reg.methods) >= 19
        assert len(reg.method_sets) >= 6

    def test_round_trip_is_lossless(self, registry_dict):
        reg = MethodRegistry.model_validate(registry_dict)
        dumped = reg.model_dump(exclude_none=True)
        assert dumped == registry_dict
