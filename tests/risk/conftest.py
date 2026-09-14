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
The two worked records from the aigov-framework's
``docs/supporting-docs/Example-Hazard-Records-Two-Systems.md``, transcribed
field for field. They are the fixtures because they are the only records
written through the whole chain so far: if the contract cannot hold them, the
contract is wrong, not the example.

Returned as plain dicts so each test can break one field.
"""

import copy

import pytest

H01 = {
    "record_id": "H-01",
    "hazard": "Delayed recognition of intracranial hemorrhage",
    "sequence_of_events": [
        {"description": "A site harmonizes CT protocols and changes a series description."},
        {
            "description": "The routing rule, keyed to that free-text field, stops matching.",
            "failure_mode": "fm-upstream-data-failure",
        },
        {
            "description": "Studies from that site are never scored and the worklist shows no flag.",
            "failure_mode": "fm-silent-incompetence",
        },
        {
            "description": "Readers accustomed to the flag read its absence as a negative result.",
            "failure_mode": "fm-automation-bias",
        },
    ],
    "hazardous_situation": (
        "A positive study sits in the routine queue with no prioritization and "
        "reduced reader suspicion relative to the pre-deployment baseline"
    ),
    "harm": {
        "patient": {"level": 5, "rationale": "A missed time-critical finding where the treatment window closes"},
        "staff": {"level": 3, "rationale": "A reader held to a read that the workflow shaped"},
        "economic": {"level": 3},
        "reputational": {"level": 4, "rationale": "A reportable event with coverage"},
    },
    "depth": {"tier": "full_safety_analysis", "obligation": "vendor"},
    "initial": {"p1": "probable", "p2": "moderate"},
    "acceptability_initial": "unacceptable",
    "controls": [
        {
            "description": "Define the eligible cohort on attributes a site cannot silently change.",
            "tier": "inherently_safe_design",
            "reduces": "p1",
            "owner": "imaging informatics lead",
            "verification": {"reference": "routing rule replay at release", "dated": "2026-08-01"},
            "validation": {"reference": "seeded protocol-name change detected", "dated": "2026-08-15"},
        },
        {
            "description": "Reconcile eligible against scored studies per site daily; alert on the coverage ratio.",
            "tier": "protective_measure",
            "reduces": "p1",
            "owner": "PACS administrator",
            "verification": {"reference": "reconciliation job evidence record", "dated": "2026-08-01"},
            "validation": {"reference": "detected within one reconciliation cycle", "dated": "2026-08-15"},
        },
        {
            "description": "The worklist renders 'not scored' as an explicit state, distinct from 'no finding'.",
            "tier": "information_for_safety",
            "reduces": "p2",
            "owner": "PACS administrator",
            "verification": {"reference": "three-state display in interface review", "dated": "2026-08-01"},
            "validation": {"reference": "reader comprehension, eight readers", "dated": "2026-08-20"},
        },
    ],
    "residual": {"p1": "remote", "p2": "moderate", "harm_level": 5},
    "acceptance": {
        "outcome": "tolerable",
        "accepting_authority": "imaging AI oversight body",
        "accepted_on": "2026-09-01",
        "revisit_on": "2027-09-01",
    },
    "watched_items": ["S-01", "S-02"],
    "reanalysis_triggers": [
        "any protocol change",
        "any new site",
        "two consecutive weeks below the coverage threshold",
        "model or version change",
    ],
}

H07 = {
    "record_id": "H-07",
    "hazard": "Denial of a service the person was entitled to",
    "sequence_of_events": [
        {
            "description": "The agent cites a medical-policy criterion that does not exist in the plan document.",
            "failure_mode": "fm-confabulation",
        },
        {
            "description": "The reviewer, signing forty determinations a shift, accepts the citation unopened.",
            "failure_mode": "fm-automation-bias",
        },
        {"description": "Volume.", "failure_mode": "fm-alert-fatigue"},
        {"description": "The denial issues."},
    ],
    "hazardous_situation": (
        "A person's request is denied on a criterion that was never in the "
        "policy, with a reviewer's signature on it"
    ),
    "harm": {
        "patient": {"level": 3},
        "staff": {"level": 4},
        "economic": {"level": 3},
        "reputational": {"level": 4},
    },
    "depth": {"tier": "full_safety_analysis", "obligation": "hybrid"},
    "initial": {"p1": "occasional", "p2": "high"},
    "acceptability_initial": "unacceptable",
    "controls": [
        {
            "description": "Retrieval-grounded generation only; an ungrounded citation cannot be drafted.",
            "tier": "inherently_safe_design",
            "reduces": "p1",
            "owner": "platform owner",
            "verification": {"reference": "grounding constraint configuration item", "dated": "2026-07-01"},
            "validation": {"reference": "50 seeded requests, zero ungrounded citations", "dated": "2026-07-20"},
        },
        {
            "description": "A denial requires the cited passage displayed inline and acknowledged before signature.",
            "tier": "protective_measure",
            "reduces": "p2",
            "owner": "utilization-management director",
            "verification": {"reference": "interface review", "dated": "2026-07-01"},
            "validation": {"reference": "blinded audit of 200 signed denials", "dated": "2026-08-10"},
        },
        {
            "description": "Reviewers are given the locally measured ungrounded-citation rate.",
            "tier": "information_for_safety",
            "reduces": "p2",
            "owner": "utilization-management director",
            "verification": {"reference": "onboarding material", "dated": "2026-07-01"},
        },
    ],
    "residual": {"p1": "improbable", "p2": "low", "harm_level": 4},
    "acceptance": {
        "outcome": "tolerable",
        "accepting_authority": "utilization-management director",
        "accepted_on": "2026-09-01",
        "revisit_on": "2027-03-01",
    },
    "watched_items": ["S-11", "S-12", "S-13", "S-14"],
    "reanalysis_triggers": [
        "supplier model replaced beneath the agent",
        "policy corpus revision",
        "prompt change",
        "throughput target change",
        "any appeal pattern by group",
    ],
}


@pytest.fixture
def h01() -> dict:
    return copy.deepcopy(H01)


@pytest.fixture
def h07() -> dict:
    return copy.deepcopy(H07)
