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
The hazard record contract (aigov-framework ADR-031 D1, ADR-006).

One record per hazardous situation carries the whole ISO 14971 chain: hazard →
sequence of events (failure modes are links in it) → hazardous situation →
harm on four dimensions → P1, P2 → controls, each tagged with its hierarchy
tier and the P it reduces → verification → validation → residual position →
acceptance against a pre-declared ceiling, with a revisit date → the watched
items that trace to it.

Ported from the markdown field contract in the aigov-framework's
``WP-RM-01-Hazard-Analysis-Report.md``, which stays the authored end: a field
added there lands here next. The Risk Register (``WP-RM-01-Risk-Register.md``)
is the same records kept current, not a second shape, so there is no
``RiskRegisterEntry``.

What this contract validates is what is checkable from one record alone.
Whether a watched item id exists in the surveillance plan, or a hazard is in
the site's catalog, needs other documents and stays with their consumers.

Derived, never stored: a record's harm level (max across dimensions) and the
depth it earns are properties, so they cannot disagree with the scores they
come from. The system rollups are in :mod:`.derive`.
"""

from datetime import date

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.failure_modes.enums import AIFailureMode
from ashmatics_datamodels.registry.enums import RegistrySourcing

from .derive import analysis_depth
from .enums import (
    DEPTH_ORDINAL,
    P1_ORDINAL,
    P2_ORDINAL,
    Acceptability,
    AnalysisDepth,
    ControlTier,
    HarmLevel,
    P1Band,
    P2Band,
    ProbabilityReduced,
)


class EventLink(AshMaticsBaseModel):
    """One link in a sequence of events, from latent hazard to exposure.

    A failure mode is named HERE, by class, and is never a record of its own.
    Most links name none: every component can perform within specification and
    still produce a hazardous situation.
    """

    description: str = Field(..., min_length=1)
    failure_mode: AIFailureMode | None = Field(
        None,
        description="The failure class this link is an instance of, if any.",
        json_schema_extra={"x_ontology_scheme": "ash:AIFailureModeScheme"},
    )


class DimensionHarm(AshMaticsBaseModel):
    """Harm on one dimension, scored against that dimension's anchors."""

    level: HarmLevel
    rationale: str | None = Field(
        None, description="What could follow, in the anchor's terms."
    )


class HarmAssessment(AshMaticsBaseModel):
    """Harm on all four ``harm_model.yaml`` dimensions. All four are required:
    an unscored dimension reads later as a zero, which is how the staff and
    economic harm the pre-ADR-020 scale could not carry went unrecorded."""

    patient: DimensionHarm
    staff: DimensionHarm
    economic: DimensionHarm
    reputational: DimensionHarm

    @property
    def level(self) -> HarmLevel:
        """The maximum across the four dimensions, never an average."""
        return HarmLevel(
            max(d.level for d in (self.patient, self.staff, self.economic, self.reputational))
        )


class DepthAssignment(AshMaticsBaseModel):
    """How deep this record is analysed, and how much of that the organization
    originates rather than reviews (ADR-020 D3/D4)."""

    tier: AnalysisDepth
    obligation: RegistrySourcing = Field(
        ...,
        description="vendor / hybrid / in_house, per "
        "registry.derive.sourcing_obligation.",
    )
    stop_rationale: str | None = Field(
        None,
        description="Required at hazard_record_only: why the analysis stops. "
        "An unstated stop is indistinguishable later from an oversight.",
    )
    safety_assessment_ref: str | None = Field(
        None,
        description="The record's entry in WP-RM-02-Safety-Assessment-Report "
        "once RM.BP02 has opened it.",
    )

    @model_validator(mode="after")
    def _stop_needs_rationale(self) -> "DepthAssignment":
        if self.tier == AnalysisDepth.HAZARD_RECORD_ONLY and not (
            self.stop_rationale and self.stop_rationale.strip()
        ):
            raise ValueError(
                "tier hazard_record_only requires stop_rationale — an unstated "
                "stop is indistinguishable later from an oversight"
            )
        return self


class ProbabilityPosition(AshMaticsBaseModel):
    """P1 and P2 on the policy's bands. Never one number."""

    p1: P1Band
    p2: P2Band


class Evidence(AshMaticsBaseModel):
    """A dated pointer to the evidence for one act."""

    reference: str = Field(..., min_length=1)
    dated: date


class RiskControl(AshMaticsBaseModel):
    """A control on this record's risk.

    Verification (the control exists and operates as specified) and validation
    (it reduces the risk in use) are two acts, in that order. ``validation`` of
    ``None`` is "not yet validated" — the expected first-pass state, and the
    commonest state in a risk file, which is why it is a field and not an
    omission.
    """

    description: str = Field(..., min_length=1)
    tier: ControlTier
    reduces: ProbabilityReduced
    owner: str = Field(..., min_length=1)
    verification: Evidence | None = None
    validation: Evidence | None = None

    @model_validator(mode="after")
    def _verified_before_validated(self) -> "RiskControl":
        if self.validation is None:
            return self
        if self.verification is None:
            raise ValueError(
                "a control cannot be validated before it is verified "
                "(verification then validation, RMP §6)"
            )
        if self.validation.dated < self.verification.dated:
            raise ValueError(
                f"validation dated {self.validation.dated} precedes "
                f"verification dated {self.verification.dated}"
            )
        return self


class ResidualPosition(ProbabilityPosition):
    """P1, P2 and harm level after controls, on the same bands."""

    harm_level: HarmLevel
    note: str | None = Field(
        None,
        description="E.g. that P1 is unchanged and the control works at P2 "
        "alone, which is legitimate and should be said.",
    )


class ResidualAcceptance(AshMaticsBaseModel):
    """Acceptance of residual risk, in the accepting authority's own name,
    against the ceiling declared before scoring. Silence is not acceptance,
    and an acceptance with no revisit date is permanent by default."""

    outcome: Acceptability
    accepting_authority: str = Field(..., min_length=1)
    accepted_on: date
    revisit_on: date

    @model_validator(mode="after")
    def _acceptable_outcome_with_future_revisit(self) -> "ResidualAcceptance":
        if self.outcome == Acceptability.UNACCEPTABLE:
            raise ValueError(
                "an unacceptable residual risk is not accepted by anyone; "
                "control it or refer it, but do not record an acceptance"
            )
        if self.revisit_on <= self.accepted_on:
            raise ValueError(
                f"revisit_on {self.revisit_on} must be after accepted_on "
                f"{self.accepted_on}"
            )
        return self


class HazardRecord(AshMaticsBaseModel):
    """One hazardous situation, through the whole chain (ADR-031 D1)."""

    record_id: str = Field(
        ...,
        pattern=r"^H-\d{2,}$",
        description="H-nn, stable for the life of the deployment.",
    )
    hazard: str = Field(..., min_length=1)
    sequence_of_events: list[EventLink] = Field(..., min_length=1)
    hazardous_situation: str = Field(
        ...,
        min_length=1,
        description="The circumstance in which a person is exposed, written "
        "so P1 can be estimated for it.",
    )
    harm: HarmAssessment
    depth: DepthAssignment
    initial: ProbabilityPosition
    acceptability_initial: Acceptability
    controls: list[RiskControl] = Field(default_factory=list)
    residual: ResidualPosition | None = None
    acceptance: ResidualAcceptance | None = None
    watched_items: list[str] = Field(
        default_factory=list,
        description="Ids of the Risk Surveillance Plan items tracing here.",
    )
    reanalysis_triggers: list[str] = Field(
        default_factory=list,
        description="Changes that reopen this record: model or version, "
        "population, site, protocol, workflow, integration, threshold.",
    )

    @property
    def harm_level(self) -> HarmLevel:
        return self.harm.level

    @property
    def earned_depth(self) -> AnalysisDepth:
        """What the harm level earns; ``depth.tier`` may go deeper, never
        shallower."""
        return analysis_depth(self.harm.level)

    @property
    def failure_modes(self) -> set[AIFailureMode]:
        return {AIFailureMode(link.failure_mode) for link in self.sequence_of_events if link.failure_mode}

    @property
    def unvalidated_controls(self) -> list[RiskControl]:
        """Verified or not, no validation yet — the list the register must be
        queryable for."""
        return [c for c in self.controls if c.validation is None]

    @model_validator(mode="after")
    def _chain_is_consistent(self) -> "HazardRecord":
        earned = self.earned_depth
        tier = AnalysisDepth(self.depth.tier)
        if DEPTH_ORDINAL[tier] < DEPTH_ORDINAL[earned]:
            raise ValueError(
                f"{self.record_id}: harm level {int(self.harm.level)} earns "
                f"{earned.value}; depth tier {tier.value} is shallower"
            )

        if self.residual is not None:
            if self.residual.harm_level > self.harm.level:
                raise ValueError(
                    f"{self.record_id}: residual harm level "
                    f"{int(self.residual.harm_level)} exceeds the scored harm "
                    f"level {int(self.harm.level)}; a control does not raise "
                    "severity — rescore the harm instead"
                )
            reduced = {ProbabilityReduced(c.reduces) for c in self.controls}
            if (
                P1_ORDINAL[P1Band(self.residual.p1)] < P1_ORDINAL[P1Band(self.initial.p1)]
                and ProbabilityReduced.P1 not in reduced
            ):
                raise ValueError(
                    f"{self.record_id}: residual P1 is lower than initial but "
                    "no control reduces P1"
                )
            if (
                P2_ORDINAL[P2Band(self.residual.p2)] < P2_ORDINAL[P2Band(self.initial.p2)]
                and ProbabilityReduced.P2 not in reduced
            ):
                raise ValueError(
                    f"{self.record_id}: residual P2 is lower than initial but "
                    "no control reduces P2"
                )

        if self.acceptance is not None:
            if self.residual is None:
                raise ValueError(
                    f"{self.record_id}: acceptance is of residual risk; score "
                    "the residual position first"
                )
            if (
                Acceptability(self.acceptance.outcome) == Acceptability.TOLERABLE
                and not self.watched_items
            ):
                raise ValueError(
                    f"{self.record_id}: tolerable with justification and "
                    "monitoring is not accepted until the surveillance plan "
                    "names what watches it (watched_items is empty)"
                )
        return self
