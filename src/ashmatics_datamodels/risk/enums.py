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
The hazard chain vocabularies (aigov-framework ADR-020, ADR-031).

Every value here is authored in the aigov-framework first and mirrored:

- harm level, dimensions and analysis depth — ``harm_model.yaml``
  (``model_metadata.scale``, ``dimensions[].id``, ``analysis_depth[].tier``);
- the P1 and P2 band vocabularies, the three acceptability outcomes and the
  control hierarchy — Risk Management Policy §4.3, §5.2 and §6
  (``policy-domain/ash-RMP-policy-TEMP.md``) and the hazard record field
  contract in ``WP-RM-01-Hazard-Analysis-Report.md``;
- the risk tier — ``ash:RiskTierScheme``, the CLF ``system.riskTier`` attribute.

CHAR ships the band VOCABULARIES; the organization sets the anchors each band
rests on (``{{p1BandAnchors}}``, ``{{p2BandAnchors}}``). So these enums fix what
the bands are called and how they order, never what "remote" means at a site.

Only :class:`RiskTier` is ontology-bound today. The rest carry no scheme, and
that is recorded per vocabulary in :mod:`.bindings` rather than left implicit.
"""

from enum import Enum, IntEnum


class HarmLevel(IntEnum):
    """
    ``harm_model.yaml`` scale, 1 negligible to 5 catastrophic (ADR-020).

    CONSEQUENCE ONLY, never risk: it is assessable before anything is known
    about how often a situation occurs, which is the only order that works for
    a system whose failure rates cannot be characterized in advance. Arabic
    numerals and the word "level" are deliberate — this is NOT an FDA or EU MDR
    device class, and "Class II" means something else to a device reviewer.

    The ordinal meaning is constant across the four dimensions, which is what
    makes the maximum coherent; the anchors differ per dimension.
    """

    NEGLIGIBLE = 1
    MINOR = 2
    SERIOUS = 3
    CRITICAL = 4
    CATASTROPHIC = 5


class HarmDimension(str, Enum):
    """``harm_model.yaml`` ``dimensions[].id`` — who or what the harm lands on.

    A hazardous situation's harm level is the MAXIMUM across these, never an
    average: averaging is how a revenue-cycle agent with no patient pathway
    scores low and is governed as though it were safe.
    """

    PATIENT = "patient"
    STAFF = "staff"
    ECONOMIC = "economic"
    REPUTATIONAL = "reputational"


class AnalysisDepth(str, Enum):
    """``harm_model.yaml`` ``analysis_depth[].tier`` — what a harm level earns.

    Assigned per hazardous situation, not per system. The mapping from harm
    level is :func:`ashmatics_datamodels.risk.derive.analysis_depth`.
    """

    HAZARD_RECORD_ONLY = "hazard_record_only"
    FAILURE_MODE_ANALYSIS = "failure_mode_analysis"
    FULL_SAFETY_ANALYSIS = "full_safety_analysis"


DEPTH_ORDINAL: dict[AnalysisDepth, int] = {
    AnalysisDepth.HAZARD_RECORD_ONLY: 1,
    AnalysisDepth.FAILURE_MODE_ANALYSIS: 2,
    AnalysisDepth.FULL_SAFETY_ANALYSIS: 3,
}


class P1Band(str, Enum):
    """
    P1 — the probability that the hazardous situation OCCURS, a property of
    this deployment (populations, sites, input types routed in, protocols a
    site can change, workflow position, integrations). RMP §4.3.

    Five bands. The worked example in the framework writes them A–E; the
    letters are a display convention, these values are the contract.
    """

    IMPROBABLE = "improbable"
    REMOTE = "remote"
    OCCASIONAL = "occasional"
    PROBABLE = "probable"
    FREQUENT = "frequent"


class P2Band(str, Enum):
    """
    P2 — the probability that harm FOLLOWS given the situation, a property of
    the pathway around the output (oversight, action authority, reversibility,
    whether an independent check still happens). RMP §4.3.

    Four bands, not five, as the policy ships them. P1 and P2 are never
    collapsed into one scale: a frequent model error with a reliable human
    catch and a rare error on an autonomous path are different risks, and one
    probability cannot say which P a control bought.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# Ordinal positions, 1 = least likely. Explicit rather than derived from member
# order so a reordering of the class body cannot silently change a derivation.
P1_ORDINAL: dict[P1Band, int] = {
    P1Band.IMPROBABLE: 1,
    P1Band.REMOTE: 2,
    P1Band.OCCASIONAL: 3,
    P1Band.PROBABLE: 4,
    P1Band.FREQUENT: 5,
}
P2_ORDINAL: dict[P2Band, int] = {
    P2Band.VERY_LOW: 1,
    P2Band.LOW: 2,
    P2Band.MODERATE: 3,
    P2Band.HIGH: 4,
}


class Acceptability(str, Enum):
    """The three outcomes a hazard record is evaluated into, initial and
    residual, against a ceiling declared BEFORE scoring (RMP §5.2).

    ``UNACCEPTABLE`` is an evaluation, never an acceptance: nobody accepts it.
    ``TOLERABLE`` is short for "tolerable with justification and monitoring",
    and is not accepted until the surveillance plan names what watches it.
    """

    ACCEPTABLE = "acceptable"
    TOLERABLE = "tolerable"
    UNACCEPTABLE = "unacceptable"


class ControlTier(str, Enum):
    """Risk control hierarchy, in ISO 14971 order (RMP §6).

    Replaces the eliminate / reduce likelihood / reduce impact / transfer ladder
    the pre-ADR-031 policy used; "transfer" is not a control of the risk to the
    person.
    """

    INHERENTLY_SAFE_DESIGN = "inherently_safe_design"
    PROTECTIVE_MEASURE = "protective_measure"
    INFORMATION_FOR_SAFETY = "information_for_safety"


class ProbabilityReduced(str, Enum):
    """Which probability a control reduces. Every control names one: a record
    whose residual P1 fell with no P1 control on it is inconsistent."""

    P1 = "p1"
    P2 = "p2"


class RiskTier(str, Enum):
    """
    ``ash:RiskTierScheme`` — the CLF ``system.riskTier`` attribute.

    Since ADR-031 D9 it DEFAULTS to a derivation from the system's hazard
    records (:func:`ashmatics_datamodels.risk.derive.system_risk_tier`) and a
    site may override it with a recorded reason. Values equal
    :class:`ashmatics_datamodels.common.enums.RiskCategory`, which the CLF note
    says it mirrors; a test holds them equal. It is a separate enum because
    ``RiskCategory`` is documented as FDA device class, and this tier is
    derived from harm and probability, never from a device class (ADR-020 D8).
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class LikelihoodBand(str, Enum):
    """The three columns of the default risk tier table: P1 and P2 ordinals
    summed (2–9) and cut at 4 and 6. Contract-level vocabulary for reading a
    derivation back; no site records it."""

    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"


class RiskTierBasis(str, Enum):
    """Which position of a hazard record a derived tier was read from.

    ``RESIDUAL`` once the record carries a residual position; ``INITIAL``
    before controls are scored, which errs high rather than low.
    """

    INITIAL = "initial"
    RESIDUAL = "residual"
