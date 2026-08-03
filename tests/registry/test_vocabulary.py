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
Registry vocabulary freeze + derivation behavior (ASHFORGE-412).

The freeze tests assert the exact value sets, not just shapes: these are
rule-engine keys, and an "innocent rename" must fail here before it reaches a
migration (SRS-REG-AC-6). Deployment is asserted as an ordered tuple because
its order is part of the contract (SRS-REG-03).
"""

import pytest

from ashmatics_datamodels.registry import (
    DeploymentStatus,
    OrgSourcingMix,
    PortfolioSizeBucket,
    RegistryAIType,
    RegistryCategory,
    RegistryDeployment,
    RegistrySourcing,
    is_clinical_use,
    org_sourcing_mix,
    portfolio_size_bucket,
)

# ── Vocabulary freeze ────────────────────────────────────────────────────────


def test_category_values_frozen():
    assert [m.value for m in RegistryCategory] == [
        "clinical",
        "operational",
        "administrative",
    ]


def test_aitype_values_frozen():
    assert [m.value for m in RegistryAIType] == [
        "predictive",
        "generative",
        "agentic",
        "other",
    ]


def test_sourcing_values_frozen():
    assert [m.value for m in RegistrySourcing] == ["vendor", "in_house", "hybrid"]


def test_deployment_values_frozen_in_order():
    # Order is meaningful: device → cloud, with the chosen-unknown sentinel last.
    assert [m.value for m in RegistryDeployment] == [
        "embedded",
        "pacs",
        "platform",
        "onprem",
        "cloud",
        "unknown",
    ]


def test_deployment_status_values_frozen():
    assert [m.value for m in DeploymentStatus] == [
        "evaluating",
        "pilot",
        "validating",
        "live",
        "paused",
        "retired",
    ]


def test_derived_vocabularies_frozen():
    assert [m.value for m in PortfolioSizeBucket] == [
        "none",
        "small",
        "medium",
        "large",
        "extensive",
    ]
    assert [m.value for m in OrgSourcingMix] == [
        "vendor_only",
        "mostly_vendor",
        "mixed",
        "mostly_internal",
        "internal_only",
    ]


# ── is_clinical_use (AC-2) ───────────────────────────────────────────────────


def test_is_clinical_use_truth_table():
    assert is_clinical_use(RegistryCategory.CLINICAL) is True
    assert is_clinical_use("clinical") is True
    assert is_clinical_use(RegistryCategory.OPERATIONAL) is False
    assert is_clinical_use("administrative") is False
    assert is_clinical_use(None) is False  # uncharacterized ⇒ no inferred obligation


def test_is_clinical_use_rejects_unknown_vocabulary():
    with pytest.raises(ValueError):
        is_clinical_use("clinical_use")  # the retired boolean's name, not a category


# ── portfolio_size_bucket (AC-3) ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, PortfolioSizeBucket.NONE),
        (1, PortfolioSizeBucket.SMALL),
        (3, PortfolioSizeBucket.SMALL),
        (4, PortfolioSizeBucket.MEDIUM),
        (10, PortfolioSizeBucket.MEDIUM),
        (11, PortfolioSizeBucket.LARGE),
        (25, PortfolioSizeBucket.LARGE),
        (26, PortfolioSizeBucket.EXTENSIVE),
        (400, PortfolioSizeBucket.EXTENSIVE),
    ],
)
def test_portfolio_size_bucket_boundaries(count, expected):
    assert portfolio_size_bucket(count) is expected


def test_portfolio_size_bucket_rejects_negative():
    with pytest.raises(ValueError):
        portfolio_size_bucket(-1)


# ── org_sourcing_mix (AC-3) ──────────────────────────────────────────────────


def test_org_sourcing_mix_empty_and_uncharacterized_yield_none():
    assert org_sourcing_mix([]) is None
    assert org_sourcing_mix([None, None]) is None


@pytest.mark.parametrize(
    ("sourcings", "expected"),
    [
        (["vendor"] * 3, OrgSourcingMix.VENDOR_ONLY),
        (["in_house"] * 3, OrgSourcingMix.INTERNAL_ONLY),
        (["hybrid"] * 4, OrgSourcingMix.MIXED),  # all-hybrid reads as mixed
        (["vendor"] * 4 + ["in_house"], OrgSourcingMix.MOSTLY_VENDOR),  # 0.8
        (["vendor"] + ["in_house"] * 4, OrgSourcingMix.MOSTLY_INTERNAL),  # 0.2
        (["vendor", "in_house"], OrgSourcingMix.MIXED),  # 0.5
        # None entries are excluded, not counted as in-house.
        (["vendor", None, None], OrgSourcingMix.VENDOR_ONLY),
    ],
)
def test_org_sourcing_mix_rollup(sourcings, expected):
    assert org_sourcing_mix(sourcings) is expected


def test_org_sourcing_mix_accepts_enum_members():
    # vendor + hybrid = (1.0 + 0.5) / 2 = 0.75, which sits ON the mostly-vendor
    # threshold (> 0.75) and therefore reads MIXED.
    assert (
        org_sourcing_mix([RegistrySourcing.VENDOR, RegistrySourcing.HYBRID])
        is OrgSourcingMix.MIXED
    )


def test_org_sourcing_mix_rejects_unknown_vocabulary():
    with pytest.raises(ValueError):
        org_sourcing_mix(["third_party"])
