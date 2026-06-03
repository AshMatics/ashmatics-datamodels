# Copyright 2025 Asher Informatics PBC
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
ADR-002 x_ontology binding guard.

Parses the FORGE + unified ontology Turtle into one rdflib graph and asserts that
every ``x_ontology_class`` / ``x_ontology_property`` / ``x_ontology_scheme``
annotation on the org models resolves to a real concept, and that every member of
a scheme-bound enum is an actual SKOS concept in that scheme. Drift between the
Pydantic contract and the ontology becomes a failed test, not a silent bug.

Ontology source resolution (in order):
  1. ``ASHMATICS_ONTOLOGY_DIR`` env var (directory holding the .ttl files);
  2. a checkout of ``ashmatics-ontology`` beside this repo;
  3. otherwise the suite is skipped (the package can't assume the sibling repo at
     an install site — productionizing this, e.g. publishing the ontology as a
     versioned artifact or vendoring a synced copy, is the ADR-002 follow-on).
"""

import os
from enum import Enum
from pathlib import Path
from typing import get_args

import pytest

# rdflib is a dev/test-only dependency (ADR-002 guard); skip cleanly if absent.
pytest.importorskip("rdflib")
from rdflib import RDF, Graph, URIRef  # noqa: E402
from rdflib.namespace import OWL, SKOS  # noqa: E402

from ashmatics_datamodels.org import OrganizationModel  # noqa: E402

# Prefixes used by x_ontology_* annotations. Asserted against the parsed graph's
# own bindings in test_prefixes_match_ontology so a stale IRI here can't pass.
PREFIXES = {
    "forge": "http://asherinformatics.com/ontology/forge#",
    "ash": "http://asherinformatics.com/ontology/ashmatics/",
    "ashcai": "https://ashmatics.com/ontology/cai#",
}

ONTOLOGY_FILES = (
    "ashmatics-unified-ontology.ttl",  # ash: + ashcai: (forge owl:imports this)
    "forge-organizational-ontology.ttl",  # forge:
)

# Models whose ADR-002 annotations this guard enforces.
ANNOTATED_MODELS = (OrganizationModel,)


def _ontology_dir() -> Path | None:
    env = os.environ.get("ASHMATICS_ONTOLOGY_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    # tests/org/<this file> -> repo root is parents[2]; sibling repo is beside it.
    repo_root = Path(__file__).resolve().parents[2]
    sibling = repo_root.parent / "ashmatics-ontology"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="module")
def graph() -> Graph:
    ontology_dir = _ontology_dir()
    if ontology_dir is None:
        pytest.skip(
            "FORGE ontology source not found. Set ASHMATICS_ONTOLOGY_DIR or check "
            "out ashmatics-ontology beside this repo to run the binding guard."
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
    """An annotated IRI must be declared AND of the expected ontology *kind*.

    Existence alone is too weak: it would let a datatype-property IRI pass in an
    x_ontology_class slot (and vice-versa) — the most likely real annotation
    mistake. This asserts the IRI carries one of the expected rdf:type values.
    """
    return any((iri, RDF.type, t) in g for t in types)


def _enum_type(annotation) -> type[Enum] | None:
    # get_args unwraps both typing.Optional/Union and PEP 604 (X | None), and
    # returns () for a bare class — so this handles required and optional enums.
    args = get_args(annotation)
    candidates = list(args) if args else [annotation]
    for candidate in candidates:
        if isinstance(candidate, type) and issubclass(candidate, Enum):
            return candidate
    return None


def _scheme_value_set(g: Graph, scheme_iri: URIRef) -> set[str]:
    """Legal values for a scheme = notations ∪ prefLabels of its SKOS concepts.

    FORGE concepts assert membership via ``rdf:type <scheme>`` (not skos:inScheme).
    """
    values: set[str] = set()
    # Concepts assert scheme membership via rdf:type <scheme> (FORGE's convention)
    # or the standard skos:inScheme — accept either so a future scheme authored the
    # conventional way is not invisible to the guard.
    concepts = set(g.subjects(RDF.type, scheme_iri)) | set(
        g.subjects(SKOS.inScheme, scheme_iri)
    )
    for concept in concepts:
        values.update(str(n) for n in g.objects(concept, SKOS.notation))
        values.update(str(label) for label in g.objects(concept, SKOS.prefLabel))
    return values


def _annotated_fields():
    """Yield (model, field_name, field_info, extra_dict) for each annotated field."""
    for model in ANNOTATED_MODELS:
        for name, info in model.model_fields.items():
            extra = info.json_schema_extra
            if isinstance(extra, dict) and (
                "x_ontology_property" in extra or "x_ontology_scheme" in extra
            ):
                yield model, name, info, extra


def test_prefixes_match_ontology(graph):
    """The CURIE prefixes this guard expands must match the ontology's own bindings."""
    bound = {prefix: str(ns) for prefix, ns in graph.namespaces()}
    for prefix, iri in PREFIXES.items():
        assert bound.get(prefix) == iri, (
            f"prefix {prefix!r}: guard expects {iri!r}, ontology binds "
            f"{bound.get(prefix)!r}"
        )


def test_class_iris_resolve(graph):
    checked = 0
    for model in ANNOTATED_MODELS:
        extra = model.model_config.get("json_schema_extra") or {}
        class_iri = extra.get("x_ontology_class")
        if class_iri:
            checked += 1
            assert _has_type(graph, _expand(class_iri), OWL.Class), (
                f"{model.__name__}: x_ontology_class {class_iri!r} is not declared "
                f"as an owl:Class in the ontology"
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
                f"{model.__name__}.{name}: x_ontology_property {prop!r} is not "
                f"declared as an owl:*Property in the ontology"
            )
    assert checked, "no x_ontology_property annotations were found to check"


def test_scheme_iris_resolve(graph):
    checked = 0
    for model, name, _info, extra in _annotated_fields():
        scheme = extra.get("x_ontology_scheme")
        if scheme:
            checked += 1
            assert _has_type(graph, _expand(scheme), SKOS.ConceptScheme), (
                f"{model.__name__}.{name}: x_ontology_scheme {scheme!r} is not "
                f"declared as a skos:ConceptScheme in the ontology"
            )
    assert checked, "no x_ontology_scheme annotations were found to check"


def test_enum_values_are_scheme_concepts(graph):
    """Every member of a scheme-bound enum must be a real concept in that scheme.

    This is the anti-drift check: it is what would have caught coreapp's three
    extra UnitGranularity values (system/enterprise/practice) that have no FORGE
    concept — see UnitGranularity's docstring.
    """
    checked = 0
    for model, name, info, extra in _annotated_fields():
        scheme = extra.get("x_ontology_scheme")
        if not scheme:
            continue
        enum_type = _enum_type(info.annotation)
        assert enum_type is not None, (
            f"{model.__name__}.{name}: has x_ontology_scheme but its type is not an "
            f"Enum"
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
