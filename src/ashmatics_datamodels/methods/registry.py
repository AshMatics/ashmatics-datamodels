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
Method-registry document contract: the full shape of the aigov-framework
``method_registry.yaml`` (metadata + methods + method sets), so the file
round-trips parse -> validate -> serialize without loss.

Cross-references that need OTHER files (tool tokens against
tooling_registry.yaml, {{system.*}} condition tokens against the CLF
registered-attribute block) stay in the aigov-framework validator; this
contract owns everything checkable from the document alone.
"""

from datetime import date

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .method_sets import MethodSet
from .methods import MethodDefinition


class RegistryMetadata(AshMaticsBaseModel):
    """The registry_metadata header block."""

    registry_id: str = Field(..., min_length=1)
    version: str = Field(
        ..., pattern=r"^\d+\.\d+\.\d+$",
        description="Registry content SemVer (independent of repo SemVer).",
    )
    status: str = Field(
        ..., description="Lifecycle status, e.g. 'pilot'."
    )
    scope: str = Field(
        ..., description="Which junction waves this registry version covers."
    )
    created: date
    last_updated: date
    review_cycle: str = Field(..., description="e.g. 'annual'.")
    adr_refs: list[str] = Field(
        ..., min_length=1,
        description="Governing ADRs (e.g. 'ADR-011', 'coreapp ADR-031').",
    )
    jira: str = Field(..., description="Tracking issue key.")


class MethodRegistry(AshMaticsBaseModel):
    """The whole method-registry document."""

    registry_metadata: RegistryMetadata
    methods: list[MethodDefinition] = Field(..., min_length=1)
    method_sets: list[MethodSet] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_internal_references(self) -> "MethodRegistry":
        method_ids = [m.method_id for m in self.methods]
        dupes = {mid for mid in method_ids if method_ids.count(mid) > 1}
        if dupes:
            raise ValueError(f"duplicate method_id values: {sorted(dupes)}")

        set_ids = [s.set_id for s in self.method_sets]
        set_dupes = {sid for sid in set_ids if set_ids.count(sid) > 1}
        if set_dupes:
            raise ValueError(f"duplicate set_id values: {sorted(set_dupes)}")

        defined = set(method_ids)
        for s in self.method_sets:
            for phase, members in s.members.items():
                missing = [m for m in members if m not in defined]
                if missing:
                    raise ValueError(
                        f"{s.set_id}: {phase} members not defined in "
                        f"methods: {missing}"
                    )
        return self
