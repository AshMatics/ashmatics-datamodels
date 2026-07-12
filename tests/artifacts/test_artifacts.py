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
Artifact-plane contract tests (ADR-006 shapes, ASHKBAPP-99 port).

Includes a field-parity check against the legacy aigov-framework file's
known shape so the port stays faithful: same fields, same requiredness,
no silent additions.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.artifacts import (
    BaseArtifact,
    CompiledView,
    DecisionRecord,
    InstanceArtifact,
    InstanceIndex,
    PracticeView,
    ToolRef,
)

NOW = datetime(2026, 7, 12, tzinfo=UTC)

# The legacy file's field inventory (ash-gov-process-model/models_pydantic/
# pydantic_models.py at reconciliation time). Parity guard: the port neither
# drops nor invents fields.
LEGACY_FIELDS = {
    "ToolRef": {"token", "label", "launch", "launch_target", "launch_params"},
    "PracticeView": {"id", "title", "activities", "tool_refs"},
    "BaseArtifact": {
        "id", "type", "semver", "title", "path", "content_hash",
        "last_updated", "normative_refs", "tokens_required",
        "outputs_contribute_to", "status", "parsed_view",
    },
    "CompiledView": {
        "artifact_id", "semver", "sections", "placeholders",
        "policy_bindings", "traceability", "citations", "practice_views",
        "embeddings_meta",
    },
    "DecisionRecord": {
        "decision_type", "decision_date", "rationale",
        "thresholds_checked", "signoffs",
    },
    "ExportRecord": {"uri", "etag", "created_at", "format"},
    "InstanceArtifact": {
        "instance_id", "tenant_id", "base_artifact_id", "base_semver",
        "schema_version", "body", "revisions", "decisions", "signoffs",
        "exports", "policy_binding_snapshot", "pv_binding_snapshot",
        "created_by", "created_at", "lifecycle_state",
    },
    "InstanceIndex": {
        "instance_id", "tenant_id", "base_artifact_id", "base_semver",
        "mongo_doc_id", "status", "created_at", "created_by", "updated_at",
        "updated_by", "key_metrics", "export_uris",
    },
}


def test_field_parity_with_legacy_file():
    import ashmatics_datamodels.artifacts as artifacts

    for name, expected in LEGACY_FIELDS.items():
        model = getattr(artifacts, name)
        actual = set(model.model_fields)
        assert actual == expected, (
            f"{name}: port drifted from legacy shape. "
            f"missing={expected - actual}, added={actual - expected}"
        )


def test_base_artifact_roundtrip():
    art = BaseArtifact(
        id=uuid4(),
        type="work_product",
        semver="1.2.0",
        title="WP-EF-01 Bias Assessment Report",
        path="blob://kb/artifacts/wp-ef-01.md",
        content_hash="sha256:abc123",
        last_updated=NOW,
    )
    assert art.status == "published"
    assert BaseArtifact.model_validate(art.model_dump()) == art


def test_base_artifact_rejects_unknown_type():
    with pytest.raises(ValidationError, match="type"):
        BaseArtifact(
            id=uuid4(),
            type="method",  # methods live in the method registry, not here
            semver="1.0.0",
            title="x",
            path="blob://x",
            content_hash="h",
            last_updated=NOW,
        )


def test_compiled_view_nests_practice_views():
    view = CompiledView(
        artifact_id=uuid4(),
        semver="1.0.0",
        practice_views=[
            PracticeView(
                id="PV.BP01a",
                title="Use case identification",
                tool_refs=[ToolRef(token="tool://kb.search")],
            )
        ],
    )
    dumped = view.model_dump()
    assert dumped["practice_views"][0]["tool_refs"][0]["launch_target"] == "UI"


def test_instance_artifact_lifecycle_and_decisions():
    inst = InstanceArtifact(
        instance_id=uuid4(),
        tenant_id=uuid4(),
        base_artifact_id=uuid4(),
        base_semver="1.2.0",
        schema_version="1.0",
        body={"sections": []},
        created_at=NOW,
        decisions=[
            DecisionRecord(decision_type="gate", decision_date=NOW)
        ],
    )
    assert inst.lifecycle_state == "draft"
    assert InstanceArtifact.model_validate(inst.model_dump()) == inst


def test_extra_fields_forbidden():
    """House-standard tightening vs the legacy plain BaseModel."""
    with pytest.raises(ValidationError):
        InstanceIndex(
            instance_id=uuid4(),
            tenant_id=uuid4(),
            base_artifact_id=uuid4(),
            base_semver="1.0.0",
            mongo_doc_id="doc-1",
            status="draft",
            created_at=NOW,
            surprise_field="nope",
        )


def test_instance_artifact_ontology_binding_resolves():
    """InstanceArtifact realizes ashcai:WorkProduct; check against the TTL
    when the sibling ontology checkout is present (ADR-002 pattern)."""
    import os
    from pathlib import Path

    pytest.importorskip("rdflib")
    from rdflib import RDF, Graph, URIRef
    from rdflib.namespace import OWL

    env = os.environ.get("ASHMATICS_ONTOLOGY_DIR")
    ontology_dir = (
        Path(env).expanduser()
        if env
        else Path(__file__).resolve().parents[2].parent / "ashmatics-ontology"
    )
    ttl = ontology_dir / "ashmatics-unified-ontology.ttl"
    if not ttl.is_file():
        pytest.skip("ontology source not found beside this repo")

    g = Graph()
    g.parse(ttl, format="turtle")
    extra = InstanceArtifact.model_config.get("json_schema_extra") or {}
    curie = extra.get("x_ontology_class")
    assert curie == "ashcai:WorkProduct"
    iri = URIRef("https://ashmatics.com/ontology/cai#" + curie.split(":")[1])
    assert (iri, RDF.type, OWL.Class) in g
