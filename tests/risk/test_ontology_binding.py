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
ADR-002 binding guard for the hazard chain vocabularies.

Iterates ``risk.bindings.RISK_BINDINGS`` the way the registry guard iterates
its table, and additionally checks the one ``x_ontology_scheme`` field
annotation the record carries (``EventLink.failure_mode``). BOUND vocabularies
are checked both ways: every member is a concept, and every concept has a
member — both bound schemes are closed facets, so a concept with no member is
a value the record cannot express.

Since 0.21.0 the record carries several ``x_ontology_scheme`` field annotations
(the failure class on four models, the signal-access mode on the watch-list row,
``HazardRecord.method_used``). ``ANNOTATED_FIELDS`` lists them, a test fails if a
model in the package gains one that is not listed, and each is resolved against
the ontology.
"""

import os
from enum import Enum
from pathlib import Path

import pytest

from ashmatics_datamodels.common.enums import SignalAccess
from ashmatics_datamodels.registry.bindings import BindingStatus
from ashmatics_datamodels.risk import (
    RISK_BINDINGS,
    EventLink,
    FailureAnalysisEntry,
    FailureClassScreening,
    FailureWatchListRow,
    HazardRecord,
)
from ashmatics_datamodels.risk import enums as risk_enums

# Every (model, field) in the hazard chain that asserts an x_ontology_scheme.
ANNOTATED_FIELDS = [
    (EventLink, "failure_mode"),
    (FailureClassScreening, "failure_mode"),
    (FailureAnalysisEntry, "failure_mode"),
    (FailureWatchListRow, "failure_mode"),
    (FailureWatchListRow, "acquisition_mode"),
    (HazardRecord, "method_used"),
]

BOUND = [b for b in RISK_BINDINGS if b.status is BindingStatus.BOUND]


def test_every_risk_vocabulary_has_a_binding_row():
    """'Unanchored' is a decision, recorded per enum, not a default."""
    declared = {b.enum for b in RISK_BINDINGS}
    public = {
        obj
        for obj in vars(risk_enums).values()
        if isinstance(obj, type)
        and issubclass(obj, Enum)
        and obj.__module__ == risk_enums.__name__
    }
    missing = {e.__name__ for e in (public | {SignalAccess}) - declared}
    assert not missing, f"risk enums with no SchemeBinding row: {sorted(missing)}"


def test_every_scheme_annotated_field_is_listed_for_the_guard():
    """A field that asserts x_ontology_scheme and is missing from
    ANNOTATED_FIELDS would be asserted and never checked."""
    import inspect

    from pydantic import BaseModel

    from ashmatics_datamodels import risk

    found = set()
    for obj in vars(risk).values():
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            for name, info in obj.model_fields.items():
                extra = info.json_schema_extra
                if isinstance(extra, dict) and "x_ontology_scheme" in extra:
                    found.add((obj, name))
    assert found == set(ANNOTATED_FIELDS)


rdflib = pytest.importorskip("rdflib")
from rdflib import RDF, Graph, URIRef  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

PREFIXES = {
    "ash": "http://asherinformatics.com/ontology/ashmatics/",
    "ashcai": "https://ashmatics.com/ontology/cai#",
}


def _ontology_dir() -> Path | None:
    env = os.environ.get("ASHMATICS_ONTOLOGY_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    sibling = Path(__file__).resolve().parents[2].parent / "ashmatics-ontology"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="module")
def graph() -> Graph:
    d = _ontology_dir()
    if d is None:
        pytest.skip(
            "ontology source not found. Set ASHMATICS_ONTOLOGY_DIR or check "
            "out ashmatics-ontology beside this repo to run the binding guard."
        )
    fpath = d / "ashmatics-unified-ontology.ttl"
    if not fpath.is_file():
        pytest.skip(f"ontology file missing: {fpath}")
    g = Graph()
    g.parse(fpath, format="turtle")
    return g


def _expand(curie: str) -> URIRef:
    prefix, _, local = curie.partition(":")
    return URIRef(PREFIXES[prefix] + local)


def _concepts(g: Graph, scheme: URIRef) -> set:
    return set(g.subjects(RDF.type, scheme)) | set(g.subjects(SKOS.inScheme, scheme))


def _local_name(iri) -> str:
    s = str(iri)
    return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]


def test_bound_schemes_resolve_and_match_both_ways(graph):
    assert BOUND, "no BOUND risk bindings to check"
    for binding in BOUND:
        scheme = _expand(binding.scheme)
        assert (scheme, RDF.type, SKOS.ConceptScheme) in graph, binding.scheme
        concepts = _concepts(graph, scheme)
        # Concept count first, so an unresolvable scheme cannot pass as empty.
        assert concepts, f"{binding.scheme} has no concepts"
        notations = {str(n) for c in concepts for n in graph.objects(c, SKOS.notation)}
        members = {m.value for m in binding.enum}
        assert members == notations, (
            f"{binding.enum.__name__} vs {binding.scheme}: "
            f"members only {sorted(members - notations)}, "
            f"concepts only {sorted(notations - members)}"
        )


def test_risk_tier_scheme_is_not_described_as_a_device_class(graph):
    """Ontology <= 2.11.0 defined the tiers as FDA Device Class I/II/III. The
    guard reads whatever ontology is checked out, so it fails against that
    version by design: the fix is ashmatics-ontology 0.18.1."""
    scheme = _expand("ash:RiskTierScheme")
    subjects = {scheme} | _concepts(graph, scheme)
    assert len(subjects) == 4, "expected the scheme and three tiers"
    for s in subjects:
        for pred in (SKOS.definition, SKOS.scopeNote):
            for text in graph.objects(s, pred):
                lowered = str(text).lower()
                assert "equivalent to fda device class" not in lowered, (s, str(text))
                assert "riskcategory" not in lowered, (s, str(text))


def test_event_link_failure_mode_scheme(graph):
    extra = EventLink.model_fields["failure_mode"].json_schema_extra
    scheme = _expand(extra["x_ontology_scheme"])
    local_names = {_local_name(c) for c in _concepts(graph, scheme)}
    from ashmatics_datamodels.failure_modes import AIFailureMode

    assert {m.value for m in AIFailureMode} == local_names


def _annotation_enum(model, field):
    """The Enum inside a field's annotation, if it has one."""
    from typing import get_args

    found = []

    def walk(candidate):
        if isinstance(candidate, type) and issubclass(candidate, Enum):
            found.append(candidate)
            return
        for arg in get_args(candidate):
            walk(arg)

    walk(model.model_fields[field].annotation)
    return found[0] if found else None


@pytest.mark.parametrize(("model", "field"), ANNOTATED_FIELDS)
def test_annotated_field_scheme_resolves_and_covers_its_enum(graph, model, field):
    extra = model.model_fields[field].json_schema_extra
    scheme = _expand(extra["x_ontology_scheme"])
    assert (scheme, RDF.type, SKOS.ConceptScheme) in graph, extra
    enum_type = _annotation_enum(model, field)
    if enum_type is None:
        # method_used is an mth:// id string: the scheme must exist, and its
        # concepts' notations are the ids. The six hazard methods are not in
        # the ontology until ASHFORGE-828, so membership is not asserted.
        return
    concepts = _concepts(graph, scheme)
    assert concepts, f"{extra['x_ontology_scheme']} has no concepts"
    legal = {_local_name(c) for c in concepts} | {
        str(n) for c in concepts for n in graph.objects(c, SKOS.notation)
    }
    members = {m.value for m in enum_type}
    assert members <= legal, (
        f"{model.__name__}.{field}: {enum_type.__name__} members not in "
        f"{extra['x_ontology_scheme']}: {sorted(members - legal)}"
    )
