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
The Failure Watch List row (SOP-RM-02 Step 13; ASHFORGE-827, coreapp ADR-061 D9).

A hazard record's ``watched_items`` began as bare ids of Risk Surveillance Plan
items. SOP-RM-02 Step 13 builds more than an id: for each credible class, what
to watch, where it is read from, how the signal reaches governance, how often,
against what threshold, who owns it, and where the acquisition is weaker than
the harm warrants. This module is that row.

``HazardRecord.watched_items`` accepts BOTH forms, so a payload written before
the row existed still validates and the row can replace the id one record at a
time. The row is a payload sub-model now; it becomes its own table only when
surveillance (SOP-RM-04) or AI Watch reads rows across records (ADR-061 D9).
"""

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel
from ashmatics_datamodels.common.enums import SignalAccess
from ashmatics_datamodels.failure_modes.enums import AIFailureMode

from .enums import HarmLevel


class FailureWatchListRow(AshMaticsBaseModel):
    """One credible failure class, watched.

    ``acquisition_mode`` is how the signal reaches governance, chosen within
    what the deployment affords (``{{system.signalAccess}}``), the highest harm
    taking the strongest. That a mode lies within the affordance, and that it
    is strong enough for ``max_harm_level``, are comparisons against the
    system's facets and stay with the consumer that holds them. When the mode
    is weaker than the harm warrants, ``shortfall`` says so: a shortfall is
    written, not quietly dropped.
    """

    failure_mode: AIFailureMode = Field(
        ...,
        description="The credible class being watched.",
        json_schema_extra={"x_ontology_scheme": "ash:AIFailureModeScheme"},
    )
    max_harm_level: HarmLevel = Field(
        ...,
        description="The highest harm level the class reaches, which ranks "
        "the row on the watch list.",
    )
    observable: str = Field(
        ..., min_length=1, description="The first signal that would show it."
    )
    source: str = Field(
        ..., min_length=1, description="Where the observable is read from."
    )
    acquisition_mode: SignalAccess = Field(
        ...,
        description="How the signal reaches governance: connected, queried, "
        "submitted or observed.",
        json_schema_extra={"x_ontology_scheme": "ash:SignalAccessScheme"},
    )
    cadence: str = Field(
        ...,
        min_length=1,
        description="How often it is read, in the plan's own words.",
    )
    threshold: str = Field(
        ...,
        min_length=1,
        description="What reading reopens the record or raises an alert.",
    )
    owner: str = Field(..., min_length=1)
    shortfall: str | None = Field(
        None,
        min_length=1,
        description="Where acquisition is weaker than the harm warrants, and "
        "what is missing. None: no shortfall.",
    )
    item_id: str | None = Field(
        None,
        min_length=1,
        description="The Risk Surveillance Plan item this row feeds, once the "
        "plan has one. The bare-id form of watched_items names the same thing.",
    )


WatchedItem = str | FailureWatchListRow
"""One entry of ``HazardRecord.watched_items``: a bare Risk Surveillance Plan
item id (every payload written before 0.21.0) or the typed row."""
