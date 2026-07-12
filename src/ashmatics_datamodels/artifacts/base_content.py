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
Base reference-content contracts (the KB side of the artifact plane).

aigov-framework ADR-006 (Policy/Process Base Persistence and Customer
Instantiation Strategy, Accepted 2025-08-11) layer 1: the Knowledge Base is
the system of record for cross-tenant base content — Markdown artifacts in
blob storage with content-addressed IDs and SemVer, metadata in Postgres,
and compiled JSON views for agent/wizard consumption.

Ported field-for-field from the aigov-framework's legacy
``ash-gov-process-model/models_pydantic/pydantic_models.py`` (ASHKBAPP-99
reconciliation; that file is now a deprecation shim re-exporting these).
The port is faithful: no fields added or removed. Inheriting
``AshMaticsBaseModel`` tightens behavior (extra fields forbidden,
assignment validation) per house standard. Ontology bindings beyond
provenance notes are deferred to the ADR-002 promotion gate — the ``type``
Literal overlaps ``ash:DocumentKindScheme`` governance kinds but with
different stored values, so binding it is a redesign, not a port.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel


class ToolRef(AshMaticsBaseModel):
    """A tool reference attached to a base practice view (tool:// token
    by convention; tokens resolve against the aigov-framework
    tooling_registry.yaml)."""

    token: str
    label: str | None = None
    launch: bool = False
    launch_target: Literal["UI", "API", "JOB"] = "UI"
    launch_params: dict[str, Any] = Field(default_factory=dict)


class PracticeView(AshMaticsBaseModel):
    """Agent/wizard-facing view of one base practice (e.g. ``PV.BP01a``)."""

    id: str = Field(..., description='Base practice ID, e.g. "PV.BP01a".')
    title: str
    activities: list[str] = Field(default_factory=list)
    tool_refs: list[ToolRef] = Field(default_factory=list)


class BaseArtifact(AshMaticsBaseModel):
    """
    KB metadata record for one base reference artifact: the Postgres row
    pointing at the Markdown source of truth in blob storage (ADR-006
    layer 1). Immutable per semver; new content = new semver.
    """

    id: UUID
    type: Literal["policy", "process", "work_product", "mapping"]
    semver: str
    title: str
    path: str = Field(
        ..., description="Blob/object storage URI of the Markdown source."
    )
    content_hash: str
    last_updated: datetime
    normative_refs: list[str] = Field(default_factory=list)
    tokens_required: dict[str, Any] = Field(default_factory=dict)
    outputs_contribute_to: list[str] = Field(default_factory=list)
    status: Literal["draft", "published"] = "published"
    parsed_view: dict[str, Any] | None = Field(
        None, description="Optional inline compiled view (JSONB in Postgres)."
    )


class CompiledView(AshMaticsBaseModel):
    """
    Compiled JSON view of a base artifact for agent/wizard consumption:
    sections, placeholders, policy bindings, and traceability, generated
    from the Markdown source at publish time (ADR-006 layer 1).
    """

    artifact_id: UUID
    semver: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    placeholders: dict[str, Any] = Field(default_factory=dict)
    policy_bindings: dict[str, Any] = Field(default_factory=dict)
    traceability: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    practice_views: list[PracticeView] = Field(default_factory=list)
    embeddings_meta: dict[str, Any] | None = None
