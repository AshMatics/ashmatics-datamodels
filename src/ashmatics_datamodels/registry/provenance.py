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
Provenance on AI System Registry attribute values (aigov-framework ADR-033 D4).

Registration copies the values intake screened on the Triage Record into the
register entry, each with where it came from, who recorded it and when. The
risk analysis later confirms or corrects them. **A correction is a new value
that names the value it supersedes, never an overwrite**, so the register can
always show what was believed when a decision was taken.

Two derivations read the history rather than a stored flag, for the same reason
``registry.derive.system_class`` does: a stored "current value" or "corrected"
field is a second answer that can disagree with the history it summarizes.

- ``current_value`` — the value in force: the one no other value supersedes.
- ``differs_from_triage`` — whether the value in force differs from what triage
  screened. Under ADR-033 D4 a correction that flips a screened attribute
  re-opens the triage route; this answers the "flips" half. Whether a raised
  harm band also re-opens it is read from the hazard records, not from here.
"""

from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel


class AttributeValueSource(str, Enum):
    """Where a registered attribute value came from."""

    TRIAGE_RECORD = "triage_record"
    AI_INVENTORY = "ai_inventory"
    RISK_REGISTER = "risk_register"


class RegisteredAttributeValue(AshMaticsBaseModel):
    """One recorded value of a ``{{system.*}}`` attribute on a register entry."""

    value_id: str = Field(..., min_length=1, description="Stable id of this recorded value.")
    attribute: str = Field(
        ..., pattern=r"^system\.[a-z][A-Za-z0-9]*$",
        description="The CLF attribute, e.g. system.actionAuthority.",
    )
    value: str | int | bool | list[str] | None = Field(
        ..., description="The value as recorded; None records 'unknown'."
    )
    source: AttributeValueSource
    source_record_id: str | None = Field(
        None,
        description="The record the value was taken from: the Triage Record id for a "
        "screened value, the hazard analysis id for a correction.",
    )
    recorded_by: str = Field(..., min_length=1, description="Who screened or recorded it.")
    recorded_at: datetime
    supersedes: str | None = Field(
        None, description="value_id of the value this one corrects, if any."
    )

    @model_validator(mode="after")
    def _provenance_is_complete(self) -> "RegisteredAttributeValue":
        if self.source == AttributeValueSource.TRIAGE_RECORD and not self.source_record_id:
            raise ValueError("a value from the triage record must name the Triage Record it came from")
        if self.supersedes is not None and self.supersedes == self.value_id:
            raise ValueError("a value cannot supersede itself")
        return self


def _for(values: Iterable[RegisteredAttributeValue], attribute: str) -> list[RegisteredAttributeValue]:
    return [v for v in values if v.attribute == attribute]


def current_value(
    values: Iterable[RegisteredAttributeValue], attribute: str
) -> RegisteredAttributeValue | None:
    """The value in force for ``attribute``: the one no other value supersedes.

    Raises ``ValueError`` when the history has more than one unsuperseded value,
    because two answers in force is a defect in the record, not a tie to break.
    Returns ``None`` when nothing is recorded.
    """
    history = _for(values, attribute)
    superseded = {v.supersedes for v in history if v.supersedes}
    in_force = [v for v in history if v.value_id not in superseded]
    if len(in_force) > 1:
        ids = ", ".join(sorted(v.value_id for v in in_force))
        raise ValueError(f"{attribute} has more than one value in force: {ids}")
    return in_force[0] if in_force else None


def differs_from_triage(values: Iterable[RegisteredAttributeValue], attribute: str) -> bool:
    """Whether the value in force differs from the value triage screened.

    ``False`` when triage did not screen the attribute, or nothing is recorded:
    there is nothing to flip.
    """
    history = _for(values, attribute)
    screened = [v for v in history if v.source == AttributeValueSource.TRIAGE_RECORD]
    if not screened:
        return False
    in_force = current_value(history, attribute)
    if in_force is None:
        return False
    first = min(screened, key=lambda v: v.recorded_at)
    return in_force.value != first.value
