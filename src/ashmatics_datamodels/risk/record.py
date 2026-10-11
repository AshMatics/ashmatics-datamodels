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

0.21.0 (ASHFORGE-827) adds, all optional so every earlier payload validates:
the method chosen for the record, a type on each link, a dimension recorded as
not reachable, the per-class failure analysis, and a typed watch-list row in
``watched_items``. The sub-models for the last two are in
:mod:`.failure_analysis` and :mod:`.watch`.
"""

from datetime import date

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.failure_modes.enums import AIFailureMode
from ashmatics_datamodels.methods.methods import MethodId
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
    LinkType,
    P1Band,
    P2Band,
    ProbabilityReduced,
)
from .failure_analysis import FailureAnalysisEntry
from .watch import FailureWatchListRow, WatchedItem


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
    link_type: LinkType | None = Field(
        None,
        description="Whether this link is technical, human or organizational. "
        "None: not typed, which is every payload written before 0.21.0.",
    )


class DimensionHarm(AshMaticsBaseModel):
    """Harm on one dimension: scored against that dimension's anchors, or
    recorded as not reachable with the reason.

    A dimension is never blank: "a dimension the situation cannot reach is
    recorded as not reachable with the reason, never left blank" (SOP-RM-01
    Step 4). So exactly one of ``level`` and ``not_reachable`` is set. A
    not-reachable dimension has no level at all rather than a placeholder one,
    so it cannot contribute to the maximum by accident or be read later as a
    zero.

    ``level`` is ``None`` only on a not-reachable dimension; every payload
    written before 0.21.0 scored all four and validates unchanged. Because the
    model validates on assignment, switch a dimension between the two states by
    replacing it whole, not by setting one field.
    """

    level: HarmLevel | None = Field(
        None, description="Required unless the dimension is not reachable."
    )
    rationale: str | None = Field(
        None, description="What could follow, in the anchor's terms."
    )
    not_reachable: bool = Field(
        False,
        description="True where the situation cannot reach this dimension.",
    )
    not_reachable_reason: str | None = Field(
        None,
        min_length=1,
        description="Why it cannot. Required when not_reachable, refused otherwise.",
    )

    @model_validator(mode="after")
    def _scored_or_not_reachable_with_reason(self) -> "DimensionHarm":
        if self.not_reachable:
            if self.level is not None:
                raise ValueError(
                    "a not-reachable dimension has no level; score it or "
                    "record it as not reachable, not both"
                )
            if not self.not_reachable_reason:
                raise ValueError(
                    "not_reachable requires not_reachable_reason: a dimension "
                    "the situation cannot reach is recorded with the reason, "
                    "never left blank"
                )
        else:
            if self.level is None:
                raise ValueError(
                    "a dimension is scored or recorded as not reachable with "
                    "the reason; it is never left blank"
                )
            if self.not_reachable_reason is not None:
                raise ValueError(
                    "not_reachable_reason is only for a dimension recorded as "
                    "not_reachable"
                )
        return self


class HarmAssessment(AshMaticsBaseModel):
    """Harm on all four ``harm_model.yaml`` dimensions. All four are present:
    an unaddressed dimension reads later as a zero, which is how the staff and
    economic harm the pre-ADR-020 scale could not carry went unrecorded. Each
    is either scored or recorded as not reachable (:class:`DimensionHarm`), and
    at least one is scored: a situation that reaches no dimension is not a
    hazardous situation, and has no harm level to derive."""

    patient: DimensionHarm
    staff: DimensionHarm
    economic: DimensionHarm
    reputational: DimensionHarm

    @property
    def level(self) -> HarmLevel:
        """The maximum across the SCORED dimensions, never an average. A
        dimension recorded as not reachable has no level and does not enter
        the maximum."""
        return HarmLevel(
            max(
                d.level
                for d in (self.patient, self.staff, self.economic, self.reputational)
                if d.level is not None
            )
        )

    @model_validator(mode="after")
    def _reaches_at_least_one_dimension(self) -> "HarmAssessment":
        if all(
            d.not_reachable
            for d in (self.patient, self.staff, self.economic, self.reputational)
        ):
            raise ValueError(
                "every dimension is recorded as not reachable; a hazardous "
                "situation reaches at least one, and the harm level is the "
                "maximum over the dimensions it does"
            )
        return self


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
    method_used: MethodId | None = Field(
        None,
        description="The hazard-analysis method chosen for this record "
        "(SOP-RM-01 Step 5), an mth:// id read by SOP-RM-02 Step 3. Shape "
        "only: whether the id is registered, and whether the site's approved "
        "set allows it, are checks against the registry and stay with the "
        "consumer. None: not yet chosen.",
        json_schema_extra={"x_ontology_scheme": "ashcai:GovernanceMethodScheme"},
    )
    method_rationale_ref: str | None = Field(
        None,
        min_length=1,
        description="Id of the event that carries the rationale for the "
        "method: what was considered, what was excluded and why. The record "
        "holds the choice; the reasoning is an event (ADR-061 D3).",
    )
    initial: ProbabilityPosition
    acceptability_initial: Acceptability
    controls: list[RiskControl] = Field(default_factory=list)
    residual: ResidualPosition | None = None
    acceptance: ResidualAcceptance | None = None
    failure_analysis: list[FailureAnalysisEntry] = Field(
        default_factory=list,
        description="SOP-RM-02 Step 2: one entry per credible failure class, "
        "for this record. Empty until the review has worked through it.",
    )
    watched_items: list[WatchedItem] = Field(
        default_factory=list,
        description="What watches this record: a bare id of a Risk "
        "Surveillance Plan item (every payload before 0.21.0), or the typed "
        "watch-list row. Both may appear in one list; read through "
        "watched_item_ids and watch_list_rows rather than restating the "
        "distinction.",
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
    def watch_list_rows(self) -> list[FailureWatchListRow]:
        """The typed rows of ``watched_items``, in order."""
        return [w for w in self.watched_items if isinstance(w, FailureWatchListRow)]

    @property
    def watched_item_ids(self) -> list[str]:
        """The Risk Surveillance Plan item ids this record names: the bare ids,
        and the ``item_id`` of each typed row that has one."""
        ids: list[str] = []
        for w in self.watched_items:
            if isinstance(w, str):
                ids.append(w)
            elif w.item_id:
                ids.append(w.item_id)
        return ids

    @property
    def unvalidated_controls(self) -> list[RiskControl]:
        """Verified or not, no validation yet — the list the register must be
        queryable for."""
        return [c for c in self.controls if c.validation is None]

    @model_validator(mode="after")
    def _chain_is_consistent(self) -> "HazardRecord":
        analysed: set[str] = set()
        for entry in self.failure_analysis:
            mode = str(entry.failure_mode)
            if mode in analysed:
                raise ValueError(
                    f"{self.record_id}: failure class {mode} is analysed "
                    "twice; one entry per credible class per record"
                )
            analysed.add(mode)

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
