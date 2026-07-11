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
ADR-002 x_ontology binding guard for the kb_documents controlled vocabularies
(ASHKBAPP-91).

Parses the unified + FORGE ontology Turtle and asserts that every
``x_ontology_scheme`` annotation on the document models resolves to a real
``skos:ConceptScheme`` and that every member of a scheme-bound enum is an actual
concept in that scheme. This is what keeps the ``document_type`` discriminator
and the ``regulatory_region`` / ``regulatory_pathway`` fields single-sourced from
the ontology: drift between the Pydantic enum and the ontology becomes a failed
test, not a silent type-filtered-read bug.

Bindings covered:
  MetadataContentBase.document_type       -> ash:DocumentKindScheme
  RegulatoryMetadataContent.regulatory_region  -> ash:RegulatoryRegionScheme
  RegulatoryMetadataContent.regulatory_pathway -> ash:RegulatoryPathwayScheme

Ontology source resolution mirrors tests/org/test_ontology_binding.py:
  1. ``ASHMATICS_ONTOLOGY_DIR`` env var; 2. a sibling ``ashmatics-ontology``
  checkout; 3. otherwise the suite is skipped.
"""

import os
from enum import Enum
from pathlib import Path
from typing import get_args

import pytest

# rdflib is a dev/test-only dependency (ADR-002 guard); skip cleanly if absent.
pytest.importorskip("rdflib")
from rdflib import RDF, Graph, URIRef  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

from ashmatics_datamodels.documents.base import MetadataContentBase  # noqa: E402
from ashmatics_datamodels.documents.regulatory import (  # noqa: E402
    RegulatoryMetadataContent,
)

# CURIE prefixes used by the x_ontology_* annotations on the document models.
# Asserted against the ontology's own bindings in test_prefixes_match_ontology.
PREFIXES = {
    "ash": "http://asherinformatics.com/ontology/ashmatics/",
    "ashcai": "https://ashmatics.com/ontology/cai#",
}

ONTOLOGY_FILES = (
    "ashmatics-unified-ontology.ttl",  # ash: + ashcai:
    "forge-organizational-ontology.ttl",  # forge: (kept for a single shared parse)
)

# Models whose ADR-002 scheme annotations this guard enforces. document_type is
# annotated on MetadataContentBase (subclasses inherit the binding); the two
# regulator fields live on RegulatoryMetadataContent.
ANNOTATED_MODELS = (MetadataContentBase, RegulatoryMetadataContent)


def _ontology_dir() -> Path | None:
    env = os.environ.get("ASHMATICS_ONTOLOGY_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    # tests/documents/<this file> -> repo root is parents[2]; sibling repo beside it.
    repo_root = Path(__file__).resolve().parents[2]
    sibling = repo_root.parent / "ashmatics-ontology"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="module")
def graph() -> Graph:
    ontology_dir = _ontology_dir()
    if ontology_dir is None:
        pytest.skip(
            "Ontology source not found. Set ASHMATICS_ONTOLOGY_DIR or check out "
            "ashmatics-ontology beside this repo to run the binding guard."
        )
    g = Graph()
    for fname in ONTOLOGY_FILES:
        fpath = ontology_dir / fname
        if not fpath.is_file():
            pytest.skip(f"ontology file missing: {fpath}")
        g.parse(fpath, format="turtle")
    return g


def _expand(curie: str) -> URIRef:
    prefix, sep, local = curie.partition(":")
    assert sep, f"annotation IRI is not a CURIE: {curie!r}"
    assert prefix in PREFIXES, f"unknown prefix in annotation IRI: {curie!r}"
    return URIRef(PREFIXES[prefix] + local)


def _has_type(g: Graph, iri: URIRef, *types: URIRef) -> bool:
    return any((iri, RDF.type, t) in g for t in types)


def _enum_type(annotation) -> type[Enum] | None:
    # get_args unwraps Optional/Union and PEP 604 (X | None); returns () for a
    # bare class, so this handles both required and optional enum fields.
    args = get_args(annotation)
    candidates = list(args) if args else [annotation]
    for candidate in candidates:
        if isinstance(candidate, type) and issubclass(candidate, Enum):
            return candidate
    return None


def _scheme_value_set(g: Graph, scheme_iri: URIRef) -> set[str]:
    """Legal values for a scheme = notations u prefLabels of its SKOS concepts.

    Accepts membership via skos:inScheme (this ontology's convention) or
    rdf:type <scheme> (the dual-typing pattern), matching the org guard.
    """
    values: set[str] = set()
    concepts = set(g.subjects(SKOS.inScheme, scheme_iri)) | set(
        g.subjects(RDF.type, scheme_iri)
    )
    for concept in concepts:
        values.update(str(n) for n in g.objects(concept, SKOS.notation))
        values.update(str(label) for label in g.objects(concept, SKOS.prefLabel))
    return values


def _annotated_scheme_fields():
    """Yield (model, field_name, field_info, scheme_curie) for scheme-bound fields."""
    for model in ANNOTATED_MODELS:
        for name, info in model.model_fields.items():
            extra = info.json_schema_extra
            if isinstance(extra, dict) and "x_ontology_scheme" in extra:
                yield model, name, info, extra["x_ontology_scheme"]


def test_prefixes_match_ontology(graph):
    """CURIE prefixes this guard expands must match the ontology's own bindings."""
    bound = {prefix: str(ns) for prefix, ns in graph.namespaces()}
    for prefix, iri in PREFIXES.items():
        assert bound.get(prefix) == iri, (
            f"prefix {prefix!r}: guard expects {iri!r}, ontology binds "
            f"{bound.get(prefix)!r}"
        )


def test_scheme_iris_resolve(graph):
    checked = 0
    for model, name, _info, scheme in _annotated_scheme_fields():
        checked += 1
        assert _has_type(graph, _expand(scheme), SKOS.ConceptScheme), (
            f"{model.__name__}.{name}: x_ontology_scheme {scheme!r} is not "
            f"declared as a skos:ConceptScheme in the ontology"
        )
    assert checked, "no x_ontology_scheme annotations were found to check"


def test_enum_values_are_scheme_concepts(graph):
    """Every member of a scheme-bound enum must be a real concept in that scheme.

    The anti-drift check: a document_type / regulatory_region / regulatory_pathway
    value with no ontology concept is exactly the mismatch that makes type-filtered
    reads return nothing (ASHKBAPP-91).
    """
    checked = 0
    for model, name, info, scheme in _annotated_scheme_fields():
        enum_type = _enum_type(info.annotation)
        assert enum_type is not None, (
            f"{model.__name__}.{name}: has x_ontology_scheme but its type is not "
            f"an Enum"
        )
        legal = _scheme_value_set(graph, _expand(scheme))
        assert legal, f"scheme {scheme!r} has no concepts in the ontology"
        for member in enum_type:
            checked += 1
            assert member.value in legal, (
                f"{model.__name__}.{name}: {enum_type.__name__}.{member.name}="
                f"{member.value!r} is not a concept of {scheme} "
                f"(legal values: {sorted(legal)})"
            )
    assert checked, "no scheme-bound enum values were checked"
