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
ADR-002 binding guard for the registry vocabularies (ASHFORGE-412).

Unlike the org guard (which walks Pydantic ``x_ontology_*`` annotations), this
guard iterates ``registry.bindings.REGISTRY_BINDINGS`` — the vocabularies have
no Pydantic contract, the persisted shape being coreapp's Django model per
ADR-036. Same teeth: a BOUND scheme must exist and cover every non-carved-out
member; a PENDING binding skips loudly so the gap is visible in every run
until the ontology work lands.

Ontology source resolution matches tests/org/test_ontology_binding.py:
``ASHMATICS_ONTOLOGY_DIR`` env var, else the sibling checkout, else skip.
"""

import os
from pathlib import Path

import pytest

# rdflib is a dev/test-only dependency (ADR-002 guard); skip cleanly if absent.
pytest.importorskip("rdflib")
from rdflib import RDF, Graph, URIRef  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

from ashmatics_datamodels.registry import REGISTRY_BINDINGS, BindingStatus  # noqa: E402
from ashmatics_datamodels.registry import enums as registry_enums  # noqa: E402

PREFIXES = {
    "forge": "http://asherinformatics.com/ontology/forge#",
    "ash": "http://asherinformatics.com/ontology/ashmatics/",
    "ashcai": "https://ashmatics.com/ontology/cai#",
}

ONTOLOGY_FILES = (
    "ashmatics-unified-ontology.ttl",  # ash: + ashcai: (forge owl:imports this)
    "forge-organizational-ontology.ttl",  # forge:
)

BOUND = [b for b in REGISTRY_BINDINGS if b.status is BindingStatus.BOUND]
PENDING = [b for b in REGISTRY_BINDINGS if b.status is BindingStatus.PENDING]


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
    assert sep, f"binding scheme is not a CURIE: {curie!r}"
    assert prefix in PREFIXES, f"unknown prefix in binding scheme: {curie!r}"
    return URIRef(PREFIXES[prefix] + local)


def _scheme_value_set(g: Graph, scheme_iri: URIRef) -> set[str]:
    """Legal values for a scheme = notations ∪ prefLabels of its concepts.

    Concepts assert membership via ``rdf:type <scheme>`` (the house convention,
    used by both forge: and ash: schemes) or standard ``skos:inScheme``.
    """
    values: set[str] = set()
    concepts = set(g.subjects(RDF.type, scheme_iri)) | set(
        g.subjects(SKOS.inScheme, scheme_iri)
    )
    for concept in concepts:
        values.update(str(n) for n in g.objects(concept, SKOS.notation))
        values.update(str(label) for label in g.objects(concept, SKOS.prefLabel))
    return values


def test_every_registry_vocabulary_has_a_binding_row():
    """Anti-oversight guard: a new vocabulary enum must declare its anchoring
    status (BOUND / PENDING / PRODUCT) — 'unanchored' is a decision, not a
    default."""
    from enum import Enum

    declared = {b.enum for b in REGISTRY_BINDINGS}
    public_enums = {
        obj
        for name, obj in vars(registry_enums).items()
        if isinstance(obj, type)
        and issubclass(obj, Enum)
        and obj is not Enum
        and obj.__module__ == registry_enums.__name__
    }
    missing = {e.__name__ for e in public_enums - declared}
    assert not missing, f"registry enums with no SchemeBinding row: {sorted(missing)}"


def test_bound_schemes_resolve(graph):
    assert BOUND, "no BOUND bindings to check"
    for binding in BOUND:
        iri = _expand(binding.scheme)
        assert (iri, RDF.type, SKOS.ConceptScheme) in graph, (
            f"{binding.enum.__name__}: scheme {binding.scheme!r} is not declared "
            f"as a skos:ConceptScheme in the ontology"
        )


def test_bound_enum_members_are_scheme_concepts(graph):
    checked = 0
    for binding in BOUND:
        legal = _scheme_value_set(graph, _expand(binding.scheme))
        assert legal, f"scheme {binding.scheme!r} has no concepts in the ontology"
        for member in binding.enum:
            checked += 1
            if member.value in binding.extra_members:
                # A carved-out product escape value must NOT gain a concept
                # silently — if it does, the carve-out is stale and this
                # failure is the reminder to retire it.
                assert member.value not in legal, (
                    f"{binding.enum.__name__}.{member.name}: {member.value!r} is "
                    f"carved out as a product extra but now exists in "
                    f"{binding.scheme} — retire the carve-out and bind it"
                )
                continue
            assert member.value in legal, (
                f"{binding.enum.__name__}.{member.name}={member.value!r} is not a "
                f"concept of {binding.scheme} (legal values: {sorted(legal)})"
            )
    assert checked, "no bound enum members were checked"


def test_pending_bindings_are_still_pending():
    """Skips loudly while anchors are being authored; when a PENDING binding's
    intended scheme lands in the ontology, flip it to BOUND in bindings.py.
    This test only keeps the gap visible — it cannot verify a scheme that has
    no CURIE yet (and so needs no ontology graph)."""
    if not PENDING:
        pytest.skip("no PENDING bindings — all vocabularies anchored or product-level")
    names = ", ".join(f"{b.enum.__name__} ({b.note.split('.')[0]})" for b in PENDING)
    pytest.skip(f"awaiting ontology anchors: {names}")
