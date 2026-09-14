# Copyright 2025 Asher Informatics PBC
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
Common enumerations shared across jurisdictions.

These enums represent concepts that are jurisdiction-agnostic or
shared across multiple regulatory frameworks.
"""

from enum import Enum


class AuthorizationStatus(str, Enum):
    """
    Lifecycle status of regulatory authorizations.

    Workflow: UNDER_REVIEW → ACTIVE → {EXPIRED | WITHDRAWN | SUSPENDED}

    Used for tracking state of 510(k) clearances, PMA approvals,
    CE Marks, and other regulatory authorizations.

    Reference: ASHMATICS Workflow Ontology
    """

    ACTIVE = "active"  # Authorization currently valid and in effect
    EXPIRED = "expired"  # Authorization past expiry date, no longer valid
    WITHDRAWN = "withdrawn"  # Authorization voluntarily withdrawn by holder
    SUSPENDED = "suspended"  # Authorization temporarily suspended by authority
    UNDER_REVIEW = "under_review"  # Application under regulatory review


class RegulatoryStatus(str, Enum):
    """
    Overall regulatory standing of a product across jurisdictions.

    Workflow: PENDING → {APPROVED | REJECTED}
    Post-Market: APPROVED → {WITHDRAWN | SUSPENDED}

    Represents product-level regulatory status, distinct from
    individual authorization status.

    Reference: ASHMATICS Workflow Ontology
    """

    APPROVED = "approved"  # Product has received regulatory approval
    PENDING = "pending"  # Product submission under regulatory review
    REJECTED = "rejected"  # Product submission rejected by authority
    WITHDRAWN = "withdrawn"  # Product voluntarily withdrawn from market
    SUSPENDED = "suspended"  # Product marketing suspended by authority


class RiskCategory(str, Enum):
    """
    General risk categorization for medical devices.

    Maps to FDA Device Class: Low (I), Moderate (II), High (III)

    Used for risk-based filtering and analysis across regulatory
    jurisdictions. Aligns with FDA device classification system.

    Reference: ASHMATICS Risk Ontology
    """

    LOW = "low"  # Minimal potential for harm (Class I devices)
    MODERATE = "moderate"  # Moderate potential requiring special controls (Class II)
    HIGH = "high"  # Significant potential for harm (Class III)


class ParsingStatus(str, Enum):
    """
    Document parsing workflow status.

    Workflow: PENDING → IN_PROGRESS → {COMPLETED | FAILED}
    Alternative: PENDING → SKIPPED

    Used for tracking AI-powered document processing, chunking,
    and knowledge graph extraction workflows.

    Reference: ASHMATICS Internal Workflow Ontology
    """

    PENDING = "pending"  # Document queued for parsing
    IN_PROGRESS = "in_progress"  # Document currently being processed
    COMPLETED = "completed"  # Document successfully parsed
    FAILED = "failed"  # Document parsing encountered errors
    SKIPPED = "skipped"  # Document intentionally not parsed


class Region(str, Enum):
    """
    Geographic regions for manufacturer categorization.

    Maps to ISO 3166-1 country codes where applicable, with custom
    regional groupings (EU, APAC, LATAM).
    """

    USA = "USA"
    EU = "EU"
    DE = "DE"
    UK = "UK"
    CHINA = "CHINA"
    APAC = "APAC"
    LATAM = "LATAM"
    AUS = "AUS"
    JP = "JP"
    KR = "KR"
    OTHER = "OTHER"


class ActionAuthority(str, Enum):
    """
    ``ash:ActionAuthorityScheme`` — what the system may do without a human in
    the loop. Minted in ontology 0.13.0 (ASHFORGE-638).

    Lives here rather than in one consumer because it classifies the SYSTEM,
    not the thing conditioning on it. Two modules condition on it today:
    failure-mode applicability (a system that acts closes a feedback loop with
    no human step in between) and, since 0.15.0, method applicability via
    ``ashcai:appliesToActionAuthority``. It was defined in ``failure_modes``
    through 0.14.0 purely because that was the first consumer, and is
    re-exported from there so existing imports keep working.

    Values are concept local names, matching the ash facet convention the
    method and failure-mode applicability axes both use.
    """

    RECOMMEND_ONLY = "aa-recommend-only"
    ACT_WITH_APPROVAL = "aa-act-with-approval"
    ACT_AUTONOMOUSLY = "aa-act-autonomously"


class SignalAccess(str, Enum):
    """
    ``ash:SignalAccessScheme`` — how a monitoring observable for a deployed AI
    system reaches governance. Minted in ontology 0.18.0 / 2.11.0 for
    aigov-framework ADR-031 D5.

    A SYSTEM facet, so it lives here beside :class:`ActionAuthority`. Read two
    ways: ``{{system.signalAccess}}`` is the set a deployment AFFORDS (an
    array), and each watched item in the CHAR Risk Surveillance Plan chooses
    one mode within that set, the highest harm taking the strongest.
    :data:`SIGNAL_ACCESS_ORDINAL` makes the strength order explicit so nothing
    depends on member order.

    Values are ``skos:notation`` (``connected``), NOT concept local names
    (``sig-connected``), unlike :class:`ActionAuthority`. The only consumers are
    the CLF attribute and the surveillance plan, and both carry notations; the
    local-name convention belongs to the method and failure-mode applicability
    axes, which this is not.

    Never call it "modality" (``inputModality`` is the data type consumed) or
    "mode" (``deploymentMode``, ``generationMode``) — both words are spent.
    """

    CONNECTED = "connected"
    QUERIED = "queried"
    SUBMITTED = "submitted"
    OBSERVED = "observed"


# Strength for surveillance, 4 strongest. A strength ordering, not a quality
# judgement of the organization (the scheme's own scopeNote).
SIGNAL_ACCESS_ORDINAL: dict[SignalAccess, int] = {
    SignalAccess.CONNECTED: 4,
    SignalAccess.QUERIED: 3,
    SignalAccess.SUBMITTED: 2,
    SignalAccess.OBSERVED: 1,
}

