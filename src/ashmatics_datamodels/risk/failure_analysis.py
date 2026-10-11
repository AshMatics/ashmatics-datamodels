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
How a class of AI system fails, worked through twice (SOP-RM-01 Step 3 and
SOP-RM-02 Step 2; ASHFORGE-827, coreapp ADR-061 D9).

Two sub-models, at two grains, both over the same ten failure classes
(:class:`~ashmatics_datamodels.failure_modes.AIFailureMode`):

- :class:`FailureClassScreening` is per SYSTEM and per class: is this class
  credible for the system, and why. :class:`FailureClassScreeningSet` is the
  whole screen, the shape stored on the risk file, because every record and the
  review read it.
- :class:`FailureAnalysisEntry` is per RECORD and per credible class: what the
  failure looks like in this system, who sees it, whether anything catches it.
  A typed list on :class:`~ashmatics_datamodels.risk.HazardRecord`.

A class is never a record of its own (it enters a sequence as
``EventLink.failure_mode``), and the taxonomy is the prompt, never the answer:
these models hold the answers a person gave.

What is checkable from the screen or the entry alone is validated. That a
class an entry names was screened CREDIBLE, or that a screen covers every
class the taxonomy lists, needs the other document and stays with its
consumers; :attr:`FailureClassScreeningSet.unscreened_classes` is the read that
answers the second.
"""

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.failure_modes.enums import AIFailureMode
from ashmatics_datamodels.methods.methods import EvidenceRef

from .enums import P1Band


class FailureClassScreening(AshMaticsBaseModel):
    """One failure class, screened for one system: credible or not, and why.

    The reason is required in BOTH directions. "Classes not applicable are
    recorded with reasons" (SOP-RM-02 Step 2): an exclusion with no reason is
    indistinguishable later from a class nobody looked at.
    """

    failure_mode: AIFailureMode = Field(
        ...,
        description="The failure class, as the taxonomy spells it (fm-*).",
        json_schema_extra={"x_ontology_scheme": "ash:AIFailureModeScheme"},
    )
    credible: bool = Field(
        ..., description="Whether the class can occur in this system's deployment."
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Why it is credible, or why it is not. Required either way.",
    )
    no_detection: bool = Field(
        False,
        description="True where nothing in CHAR would currently surface this "
        "class (the taxonomy's detectable_by is empty for it). A finding, "
        "kept visible rather than defaulted away.",
    )
    evidence_refs: list[EvidenceRef] = Field(
        default_factory=list,
        description="Literature or standards the screening rests on, in the "
        "shape the taxonomy's evidence_basis uses.",
    )


class FailureClassScreeningSet(AshMaticsBaseModel):
    """The failure-class screen of one system: at most one entry per class.

    Partial states are legitimate and storable: the screen is built one class
    at a time, so this does not require all ten. Read
    :attr:`unscreened_classes` or :attr:`is_complete` for that.
    """

    screenings: list[FailureClassScreening] = Field(default_factory=list)

    @property
    def credible_classes(self) -> set[AIFailureMode]:
        return {AIFailureMode(s.failure_mode) for s in self.screenings if s.credible}

    @property
    def unscreened_classes(self) -> list[AIFailureMode]:
        """Taxonomy classes with no entry yet, in taxonomy order."""
        screened = {AIFailureMode(s.failure_mode) for s in self.screenings}
        return [m for m in AIFailureMode if m not in screened]

    @property
    def is_complete(self) -> bool:
        return not self.unscreened_classes

    @model_validator(mode="after")
    def _one_entry_per_class(self) -> "FailureClassScreeningSet":
        seen: set[str] = set()
        for s in self.screenings:
            mode = str(s.failure_mode)
            if mode in seen:
                raise ValueError(f"failure class {mode} is screened twice")
            seen.add(mode)
        return self


class FailureAnalysisEntry(AshMaticsBaseModel):
    """One credible failure class, analysed for one hazard record (SOP-RM-02
    Step 2): the class made specific to this system.

    ``no_catching_control`` and ``no_observable`` exist because "none" is a
    finding, not an omission: "a class with no observable is recorded as a
    finding" (RM-02 Step 2). Leaving ``catching_control`` or ``observable``
    ``None`` means not yet asked; setting the flag says it was asked and the
    answer is nothing.
    """

    failure_mode: AIFailureMode = Field(
        ...,
        description="The credible class this entry analyses.",
        json_schema_extra={"x_ontology_scheme": "ash:AIFailureModeScheme"},
    )
    appearance: str = Field(
        ...,
        min_length=1,
        description="What the failure looks like in THIS system, in the "
        "system's own terms; the taxonomy's generic presentation is the prompt.",
    )
    operator_view: str | None = Field(
        None, description="What the operator would actually see."
    )
    failed_output_distinguishable: bool | None = Field(
        None,
        description="Whether the operator could tell a failed output from a "
        "sound one. None: not yet established.",
    )
    affected_person_experience: str | None = None
    organization_experience: str | None = None
    severity_rank: int | None = Field(
        None,
        ge=1,
        description="The expert's ranking of this class among the record's "
        "analysed classes by severity, 1 = worst. Ties are allowed.",
    )
    revised_p1: P1Band | None = Field(
        None,
        description="P1 for this record after considering this class, where "
        "the analysis moves it. A proposal to rescore, not a rescoring: the "
        "record's own initial position is changed only by recording it.",
    )
    catching_control: str | None = Field(
        None, description="The control on this record that would catch it."
    )
    no_catching_control: bool = Field(
        False, description="Asked, and nothing catches it."
    )
    observable: str | None = Field(
        None, description="The first signal that would show it was happening."
    )
    observable_source: str | None = Field(
        None, description="Where that signal is read from."
    )
    no_observable: bool = Field(
        False, description="Asked, and there is no observable. A finding."
    )

    @model_validator(mode="after")
    def _none_is_not_also_something(self) -> "FailureAnalysisEntry":
        if self.no_catching_control and self.catching_control:
            raise ValueError(
                "no_catching_control and catching_control contradict each "
                "other; say that nothing catches it, or name what does"
            )
        if self.no_observable and (self.observable or self.observable_source):
            raise ValueError(
                "no_observable and an observable contradict each other; say "
                "there is no signal, or name it"
            )
        if self.observable_source and not self.observable:
            raise ValueError(
                "observable_source needs the observable it is the source of"
            )
        return self
