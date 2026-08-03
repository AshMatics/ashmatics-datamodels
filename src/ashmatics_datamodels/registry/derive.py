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
Derivations over the registry vocabularies (ASHFORGE-412 AC-2 / AC-3).

Four quantities that older specs treated as stored fields are defined here as
pure functions instead, so the registry stays the single written source and
every consumer computes the same answer:

- ``clinical_use`` (SRS-REG-03's boolean) — derived from the category triad;
- the obligation triad (SRS-REG-15a) — derived from the sourcing channel;
- ``ai_portfolio_size`` — derived from the active-entry count;
- ``ai_sourcing`` (org-level) — derived from per-system obligation values.

Invalid vocabulary values raise ``ValueError`` rather than degrade — the same
fail-loudly posture as the AC-4 guard.
"""

from collections.abc import Iterable

from .enums import (
    OrgSourcingMix,
    PortfolioSizeBucket,
    RegistryCategory,
    RegistrySourcing,
    SourcingChannel,
)


def is_clinical_use(category: RegistryCategory | str | None) -> bool:
    """SRS-REG-03's ``clinical_use``, resolved as a derivation (AC-2).

    The boolean is the rule-bearing edge (clinical vs. everything else); the
    stored value is the three-way :class:`RegistryCategory`. ``None`` — an
    uncharacterized entry — is ``False``: no obligation is inferred until the
    customer classifies the system.
    """
    if category is None:
        return False
    return RegistryCategory(category) is RegistryCategory.CLINICAL


def portfolio_size_bucket(active_count: int) -> PortfolioSizeBucket:
    """Bucket an active-registry-entry count (AC-3; ranges from the Stage A
    q_ai_portfolio_size options: 0 / 1–3 / 4–10 / 11–25 / 26+)."""
    if active_count < 0:
        raise ValueError(f"active_count must be >= 0, got {active_count}")
    if active_count == 0:
        return PortfolioSizeBucket.NONE
    if active_count <= 3:
        return PortfolioSizeBucket.SMALL
    if active_count <= 10:
        return PortfolioSizeBucket.MEDIUM
    if active_count <= 25:
        return PortfolioSizeBucket.LARGE
    return PortfolioSizeBucket.EXTENSIVE


def sourcing_obligation(
    channel: SourcingChannel | str | None,
    *,
    locally_adapted: bool = False,
) -> RegistrySourcing | None:
    """SRS-REG-15a's obligation triad, resolved as a derivation (decision
    2026-08-03): the customer answers the observable question (how was it
    acquired), and the obligation reading follows.

    Commercial and EHR-embedded systems carry a vendor obligation; homegrown
    and research systems put it on the customer — including commissioned or
    consultancy-built systems, which are HOMEGROWN by definition.
    ``locally_adapted`` marks a vendor-channel system the org has tuned or
    retrained, which is the only path to ``HYBRID``; on a customer-obligation
    channel it changes nothing (the obligation is already theirs).
    ``None`` — an uncharacterized entry — derives ``None``.
    """
    if channel is None:
        return None
    vendor_side = {SourcingChannel.COMMERCIAL, SourcingChannel.EHR_EMBEDDED}
    if SourcingChannel(channel) in vendor_side:
        return RegistrySourcing.HYBRID if locally_adapted else RegistrySourcing.VENDOR
    return RegistrySourcing.IN_HOUSE


def org_sourcing_mix(
    sourcings: Iterable[RegistrySourcing | str | None],
) -> OrgSourcingMix | None:
    """Roll per-system sourcing up to the org-level mix (AC-3).

    Uncharacterized entries (``None``) are excluded; returns ``None`` when no
    entry is characterized — an org answer must not be fabricated from
    nothing. ``HYBRID`` counts half vendor, half in-house. Thresholds mirror
    the Stage A option labels (>75% either way = "mostly"): an all-hybrid
    portfolio lands on ``MIXED``, which is the honest reading.
    """
    weight = {
        RegistrySourcing.VENDOR: 1.0,
        RegistrySourcing.HYBRID: 0.5,
        RegistrySourcing.IN_HOUSE: 0.0,
    }
    values = [RegistrySourcing(s) for s in sourcings if s is not None]
    if not values:
        return None
    vendor_fraction = sum(weight[v] for v in values) / len(values)
    if vendor_fraction == 1.0:
        return OrgSourcingMix.VENDOR_ONLY
    if vendor_fraction > 0.75:
        return OrgSourcingMix.MOSTLY_VENDOR
    if vendor_fraction >= 0.25:
        return OrgSourcingMix.MIXED
    if vendor_fraction > 0.0:
        return OrgSourcingMix.MOSTLY_INTERNAL
    return OrgSourcingMix.INTERNAL_ONLY
