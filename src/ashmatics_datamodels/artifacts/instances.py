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
Tenant instantiation contracts (the coreapp side of the artifact plane).

aigov-framework ADR-006 layer 2: coreapp is the system of record for
tenant-specific instantiations — full instance bodies in MongoDB
(append-only, schema-versioned), relational index rows in Postgres, and
binary exports in blob storage. Instances reference base artifacts by
stable KB artifact_id + semver and snapshot the policy/PV bindings used at
generation time.

Ported field-for-field from the aigov-framework's legacy
``ash-gov-process-model/models_pydantic/pydantic_models.py`` (ASHKBAPP-99
reconciliation). ``InstanceArtifact`` carries the one clean ontology
binding: it realizes ``ashcai:WorkProduct`` ("customer work product
instance derived from template", subclass of ``prov:Entity``).
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from ashmatics_datamodels.common.base import AshMaticsBaseModel


class DecisionRecord(AshMaticsBaseModel):
    """One governance decision captured against an instance artifact."""

    decision_type: str = Field(
        ..., description='Decision kind, e.g. "go/no-go", "gate".'
    )
    decision_date: datetime
    rationale: str | None = None
    thresholds_checked: dict[str, Any] = Field(default_factory=dict)
    signoffs: list[dict[str, Any]] = Field(default_factory=list)


class ExportRecord(AshMaticsBaseModel):
    """A rendered export (PDF/HTML/...) of an instance artifact."""

    uri: str
    etag: str | None = None
    created_at: datetime
    format: str | None = Field(None, description="e.g. PDF, HTML.")


class InstanceArtifact(AshMaticsBaseModel):
    """
    A tenant's instantiated governance artifact: the full instance document
    (Mongo body) plus revisions, decisions, sign-offs, exports, and the
    policy/PV binding snapshots taken at generation time (ADR-006 layer 2).
    """

    model_config = ConfigDict(
        json_schema_extra={"x_ontology_class": "ashcai:WorkProduct"}
    )

    instance_id: UUID
    tenant_id: UUID
    base_artifact_id: UUID
    base_semver: str
    schema_version: str
    body: dict[str, Any] = Field(
        ..., description="Full instance document (append-only in Mongo)."
    )
    revisions: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[DecisionRecord] = Field(default_factory=list)
    signoffs: list[dict[str, Any]] = Field(default_factory=list)
    exports: list[ExportRecord] = Field(default_factory=list)
    policy_binding_snapshot: dict[str, Any] = Field(default_factory=dict)
    pv_binding_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime
    lifecycle_state: Literal["draft", "approved", "retired"] = "draft"


class InstanceIndex(AshMaticsBaseModel):
    """
    Postgres index row for an instance artifact: relational references and
    reporting-friendly metadata pointing at the Mongo body (ADR-006
    layer 2).
    """

    instance_id: UUID
    tenant_id: UUID
    base_artifact_id: UUID
    base_semver: str
    mongo_doc_id: str
    status: Literal["draft", "approved", "retired"]
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
    key_metrics: dict[str, Any] = Field(default_factory=dict)
    export_uris: list[str] = Field(default_factory=list)
