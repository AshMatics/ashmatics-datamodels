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
ADR-002 x_ontology binding guard for the methods module (ASHKBAPP-99).

Same contract as ``tests/org/test_ontology_binding.py``: every
``x_ontology_*`` annotation must resolve in the parsed Turtle, and every
member of a scheme-bound enum must be a concept of that scheme. This
replaces the static SKOS snapshot the aigov-framework carried in
``validate_method_registry.py`` as its Phase 2 stopgap.

One deliberate difference from the org guard: legal enum values here also
include the concept IRI **local names**. The ash facet concepts'
``skos:notation`` values predate CHAR and differ from the local names
(``"predictive"`` vs ``ap-predictive``); the CHAR registry and CLF
condition grammar standardized on local names as concept IDs
(method_registry.yaml header; ontology ADR-006 consequences). Notations
still count, so ``MethodFamily`` (whose scheme mints notation = registry
key) checks under the same rule.
"""

import os
from enum import Enum
from pathlib import Path
from typing import get_args

import pytest

pytest.importorskip("rdflib")
from rdflib import RDF, Graph, URIRef  # noqa: E402
from rdflib.namespace import OWL, SKOS  # noqa: E402

from ashmatics_datamodels.methods import (  # noqa: E402
    ApplicabilityProfile,
    MethodDefinition,
)

PREFIXES = {
    "ash": "http://asherinformatics.com/ontology/ashmatics/",
    "ashcai": "https://ashmatics.com/ontology/cai#",
}

ONTOLOGY_FILE = "ashmatics-unified-ontology.ttl"

# Models whose ADR-002 field annotations this guard enforces.
FIELD_ANNOTATED_MODELS = (MethodDefinition, ApplicabilityProfile)
# Models carrying a model-level x_ontology_class annotation.
CLASS_ANNOTATED_MODELS = (MethodDefinition,)


def _ontology_dir() -> Path | None:
    env = os.environ.get("ASHMATICS_ONTOLOGY_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    repo_root = Path(__file__).resolve().parents[2]
    sibling = repo_root.parent / "ashmatics-ontology"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="module")
def graph() -> Graph:
    ontology_dir = _ontology_dir()
    if ontology_dir is None:
        pytest.skip(
            "ontology source not found. Set ASHMATICS_ONTOLOGY_DIR or check "
            "out ashmatics-ontology beside this repo to run the binding guard."
        )
    fpath = ontology_dir / ONTOLOGY_FILE
    if not fpath.is_file():
        pytest.skip(f"ontology file missing: {fpath}")
    g = Graph()
    g.parse(fpath, format="turtle")
    return g


def _expand(curie: str) -> URIRef:
    prefix, sep, local = curie.partition(":")
    assert sep, f"annotation IRI is not a CURIE: {curie!r}"
    assert prefix in PREFIXES, f"unknown prefix in annotation IRI: {curie!r}"
    return URIRef(PREFIXES[prefix] + local)


def _has_type(g: Graph, iri: URIRef, *types: URIRef) -> bool:
    return any((iri, RDF.type, t) in g for t in types)


def _local_name(iri: URIRef) -> str:
    s = str(iri)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    return s.rsplit("/", 1)[-1]


def _enum_types(annotation) -> list[type[Enum]]:
    """Collect Enum classes anywhere in a possibly nested annotation
    (handles ``list[X] | None``, which the org guard's flat unwrap does not).
    """
    found: list[type[Enum]] = []

    def walk(candidate) -> None:
        if isinstance(candidate, type) and issubclass(candidate, Enum):
            found.append(candidate)
            return
        for arg in get_args(candidate):
            walk(arg)

    walk(annotation)
    return found


def _scheme_value_set(g: Graph, scheme_iri: URIRef) -> set[str]:
    """Legal values = notations ∪ prefLabels ∪ IRI local names of the
    scheme's concepts (local names per this module's docstring)."""
    values: set[str] = set()
    concepts = set(g.subjects(RDF.type, scheme_iri)) | set(
        g.subjects(SKOS.inScheme, scheme_iri)
    )
    for concept in concepts:
        values.add(_local_name(concept))
        values.update(str(n) for n in g.objects(concept, SKOS.notation))
        values.update(str(lbl) for lbl in g.objects(concept, SKOS.prefLabel))
    return values


def _annotated_fields():
    for model in FIELD_ANNOTATED_MODELS:
        for name, info in model.model_fields.items():
            extra = info.json_schema_extra
            if isinstance(extra, dict) and (
                "x_ontology_property" in extra or "x_ontology_scheme" in extra
            ):
                yield model, name, info, extra


def test_prefixes_match_ontology(graph):
    bound = {prefix: str(ns) for prefix, ns in graph.namespaces()}
    for prefix, iri in PREFIXES.items():
        assert bound.get(prefix) == iri, (
            f"prefix {prefix!r}: guard expects {iri!r}, ontology binds "
            f"{bound.get(prefix)!r}"
        )


def test_class_iris_resolve(graph):
    checked = 0
    for model in CLASS_ANNOTATED_MODELS:
        extra = model.model_config.get("json_schema_extra") or {}
        class_iri = extra.get("x_ontology_class")
        if class_iri:
            checked += 1
            assert _has_type(graph, _expand(class_iri), OWL.Class), (
                f"{model.__name__}: x_ontology_class {class_iri!r} is not "
                f"declared as an owl:Class in the ontology"
            )
    assert checked, "no x_ontology_class annotations were found to check"


def test_property_iris_resolve(graph):
    checked = 0
    for model, name, _info, extra in _annotated_fields():
        prop = extra.get("x_ontology_property")
        if prop:
            checked += 1
            assert _has_type(
                graph,
                _expand(prop),
                OWL.ObjectProperty,
                OWL.DatatypeProperty,
                OWL.AnnotationProperty,
            ), (
                f"{model.__name__}.{name}: x_ontology_property {prop!r} is "
                f"not declared as an owl:*Property in the ontology"
            )
    assert checked, "no x_ontology_property annotations were found to check"


def test_scheme_iris_resolve(graph):
    checked = 0
    for model, name, _info, extra in _annotated_fields():
        scheme = extra.get("x_ontology_scheme")
        if scheme:
            checked += 1
            assert _has_type(graph, _expand(scheme), SKOS.ConceptScheme), (
                f"{model.__name__}.{name}: x_ontology_scheme {scheme!r} is "
                f"not declared as a skos:ConceptScheme in the ontology"
            )
    assert checked, "no x_ontology_scheme annotations were found to check"


def test_enum_values_are_scheme_concepts(graph):
    """The anti-drift check: every member of a scheme-bound enum must be a
    real concept in that scheme in the pinned ontology source."""
    checked = 0
    for model, name, info, extra in _annotated_fields():
        scheme = extra.get("x_ontology_scheme")
        if not scheme:
            continue
        enum_types = _enum_types(info.annotation)
        assert enum_types, (
            f"{model.__name__}.{name}: has x_ontology_scheme but no Enum in "
            f"its type"
        )
        legal = _scheme_value_set(graph, _expand(scheme))
        assert legal, f"scheme {scheme!r} has no concepts in the ontology"
        for enum_type in enum_types:
            for member in enum_type:
                checked += 1
                assert member.value in legal, (
                    f"{model.__name__}.{name}: {enum_type.__name__}."
                    f"{member.name}={member.value!r} is not a concept of "
                    f"{scheme}"
                )
    assert checked, "no scheme-bound enum values were checked"


def test_facet_enums_cover_their_schemes(graph):
    """Reverse completeness: these enums claim to single-source their facet
    vocabularies, so a concept added to the ontology without a matching enum
    member is drift too (the direction the org UnitGranularity incident ran
    the other way)."""
    seen_schemes: dict[str, list[type[Enum]]] = {}
    for _model, _name, info, extra in _annotated_fields():
        scheme = extra.get("x_ontology_scheme")
        # GovernanceMethodScheme legitimately grows method concepts without
        # the family enum changing; only facet schemes are 1:1.
        if not scheme or scheme == "ashcai:GovernanceMethodScheme":
            continue
        seen_schemes.setdefault(scheme, []).extend(_enum_types(info.annotation))
    assert seen_schemes, "no facet schemes found to check"
    for scheme, enum_types in seen_schemes.items():
        concepts = set(graph.subjects(RDF.type, _expand(scheme))) | set(
            graph.subjects(SKOS.inScheme, _expand(scheme))
        )
        concept_ids = {_local_name(c) for c in concepts}
        enum_values = {m.value for et in enum_types for m in et}
        missing = concept_ids - enum_values
        assert not missing, (
            f"{scheme}: ontology concepts with no enum member: "
            f"{sorted(missing)} — extend the enum (single-sourcing)"
        )
