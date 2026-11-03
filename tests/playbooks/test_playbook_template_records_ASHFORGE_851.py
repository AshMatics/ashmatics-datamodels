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

"""The record of one playbook template version (0.25.1, ASHFORGE-851).

The fixture is hand-written in the shape of a coreapp catalogue entry and a published
interior.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.playbooks import (
    PlaybookTemplateFacets,
    PlaybookTemplateStatus,
    PlaybookTemplateVersionRecord,
    PlaybookTemplateVersionSummary,
)

HASH = "948c86a6e660d947451a150fa7eb73e119083fac89220254584f12068163a34a"


def document() -> dict:
    return {
        "grammar_version": "1.1",
        "lanes": [{"id": "curator"}],
        "nodes": [{"id": "t0"}, {"id": "a1"}],
        "edges": [{"from": "t0", "to": "a1", "aff": "fixed"}],
        "slot_kinds": {},
    }


def facets() -> dict:
    return {
        "name": "Policy Authoring & Lifecycle",
        "intent": "Authors, ratifies and revises your AI policy set.",
        "tier": "core",
        "playbook_class": "governance",
        "phase": "always",
        "cadence": "constitutional",
        "subject_type": "organization",
        "run_cardinality": "single",
        "process_domains": ["ORG", "OVR"],
        "base_practices": ["ORG.BP03", "OVR.BP01"],
        "capability_areas": [1],
        "produces": [],
        "needs": [],
        "exchanges": [{"system": "Document management", "direction": "out"}],
        "signed_off": True,
    }


def record(**overrides) -> dict:
    fields = {
        "slug": "PBT-GOV-POLICY-01",
        "version": "0.10",
        "status": "published",
        "grammar_version": "1.1",
        "document": document(),
        "content_hash": HASH,
        "facets": facets(),
        "published_at": "2026-08-27T03:30:56.638632+00:00",
    }
    fields.update(overrides)
    return fields


def draft(**overrides) -> dict:
    return record(status="draft", content_hash=None, published_at=None) | overrides


def without_document(fields: dict) -> dict:
    return {key: value for key, value in fields.items() if key != "document"}


class TestStatus:
    def test_three_states(self):
        assert [s.value for s in PlaybookTemplateStatus] == [
            "draft",
            "published",
            "retired",
        ]

    def test_an_unknown_state_is_refused(self):
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(**record(status="deprecated"))


class TestFacets:
    def test_all_optional(self):
        assert PlaybookTemplateFacets().name is None

    def test_declared_and_extra_keys_kept(self):
        parsed = PlaybookTemplateFacets(**facets())
        dumped = parsed.model_dump()
        assert parsed.capability_areas == [1]
        assert dumped["exchanges"] == facets()["exchanges"]
        assert dumped["signed_off"] is True

    def test_a_declared_key_is_still_typed(self):
        with pytest.raises(ValidationError):
            PlaybookTemplateFacets(capability_areas=["one"])

    def test_a_catalogue_key_the_model_does_not_know_is_kept(self):
        assert PlaybookTemplateFacets(fan_out=True).model_dump()["fan_out"] is True


class TestRecord:
    def test_parses(self):
        parsed = PlaybookTemplateVersionRecord(**record())
        assert parsed.status == "published"
        assert parsed.published_at == datetime(
            2026, 8, 27, 3, 30, 56, 638632, tzinfo=UTC
        )
        assert parsed.facets.tier == "core"

    def test_json_round_trip(self):
        parsed = PlaybookTemplateVersionRecord(**record())
        assert (
            PlaybookTemplateVersionRecord.model_validate_json(parsed.model_dump_json())
            == parsed
        )

    def test_an_unknown_field_is_refused(self):
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(**record(design_status="published"))

    @pytest.mark.parametrize(
        "slug", ["PBT-GOV-POLICY-01", "PBT-FORM-ALGOVIG-01", "PBT-USE-M3-02"]
    )
    def test_slug_accepted(self, slug):
        assert PlaybookTemplateVersionRecord(**record(slug=slug)).slug == slug

    @pytest.mark.parametrize(
        "slug",
        [
            "HAZARD-01",
            "pbt-gov-policy-01",
            "PBT-GOV-01",
            "PBT-GOV-POL-ICY-01",
            "PBT-GOV-POLICY-٠١",
        ],
    )
    def test_slug_refused(self, slug):
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(**record(slug=slug))

    @pytest.mark.parametrize("version", ["1", "0.10", "1.2.3"])
    def test_version_accepted(self, version):
        assert (
            PlaybookTemplateVersionRecord(**record(version=version)).version == version
        )

    @pytest.mark.parametrize(
        "version", ["", "v1", "1.", ".1", "1..2", "1.x", "٠.١", "1." + "0" * 19]
    )
    def test_version_refused(self, version):
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(**record(version=version))

    @pytest.mark.parametrize("bad", ["abc", HASH[:-1], HASH.upper()])
    def test_content_hash_shape(self, bad):
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(**record(content_hash=bad))

    def test_change_note_length(self):
        assert PlaybookTemplateVersionRecord(**record(change_note="x" * 300))
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(**record(change_note="x" * 301))


class TestDocument:
    @pytest.mark.parametrize("key", ["lanes", "nodes", "edges"])
    def test_required_keys(self, key):
        body = document()
        del body[key]
        with pytest.raises(ValidationError, match=key):
            PlaybookTemplateVersionRecord(**record(document=body))

    def test_other_keys_are_optional_and_kept(self):
        body = document()
        del body["slot_kinds"]
        body["phase_names"] = {"1": "Plan"}
        parsed = PlaybookTemplateVersionRecord(**record(document=body))
        assert parsed.document == body

    def test_held_as_given(self):
        """content_hash is a function of the document, so nothing here may rewrite it."""
        body = document() | {" spaced key ": " spaced value ", "big": 1e16}
        parsed = PlaybookTemplateVersionRecord(**record(document=body))
        assert parsed.document == body
        assert list(parsed.document) == list(body)


class TestStateRules:
    @pytest.mark.parametrize("status", ["published", "retired"])
    @pytest.mark.parametrize("missing", ["content_hash", "published_at"])
    def test_published_and_retired_need_both(self, status, missing):
        with pytest.raises(ValidationError, match="content_hash and published_at"):
            PlaybookTemplateVersionRecord(**record(status=status, **{missing: None}))

    def test_retired_parses(self):
        assert (
            PlaybookTemplateVersionRecord(**record(status="retired")).status
            == "retired"
        )

    def test_a_draft_has_no_hash(self):
        assert PlaybookTemplateVersionRecord(**draft()).content_hash is None
        with pytest.raises(ValidationError, match="a draft has no content_hash"):
            PlaybookTemplateVersionRecord(**draft(content_hash=HASH))

    def test_checked_on_assignment(self):
        parsed = PlaybookTemplateVersionRecord(**draft())
        with pytest.raises(ValidationError):
            parsed.status = PlaybookTemplateStatus.PUBLISHED


class TestBaseLink:
    def test_both(self):
        parsed = PlaybookTemplateVersionRecord(
            **record(variant_of="PBT-GOV-POLICY-02", base_version="0.3")
        )
        assert parsed.variant_of == "PBT-GOV-POLICY-02"

    def test_neither(self):
        assert PlaybookTemplateVersionRecord(**record()).variant_of is None

    @pytest.mark.parametrize(
        "link", [{"variant_of": "PBT-GOV-POLICY-02"}, {"base_version": "0.3"}]
    )
    def test_one_alone_is_refused(self, link):
        with pytest.raises(ValidationError, match="both or neither"):
            PlaybookTemplateVersionRecord(**record(**link))

    def test_not_itself(self):
        with pytest.raises(ValidationError, match="variant of itself"):
            PlaybookTemplateVersionRecord(
                **record(variant_of="PBT-GOV-POLICY-01", base_version="0.10")
            )

    def test_an_earlier_version_of_the_same_slug_is_allowed(self):
        assert PlaybookTemplateVersionRecord(
            **record(variant_of="PBT-GOV-POLICY-01", base_version="0.9")
        )

    def test_shapes_are_checked(self):
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(
                **record(variant_of="HAZARD-01", base_version="0.3")
            )
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionRecord(
                **record(variant_of="PBT-GOV-POLICY-02", base_version="v3")
            )


class TestSummary:
    def test_has_no_document(self):
        assert "document" not in PlaybookTemplateVersionSummary.model_fields
        with pytest.raises(ValidationError):
            PlaybookTemplateVersionSummary(**record())

    def test_is_the_record_without_it(self):
        parsed = PlaybookTemplateVersionRecord(**record())
        summary = PlaybookTemplateVersionSummary(
            **parsed.model_dump(exclude={"document"})
        )
        assert summary.model_dump() == parsed.model_dump(exclude={"document"})

    def test_same_rules(self):
        with pytest.raises(ValidationError, match="content_hash and published_at"):
            PlaybookTemplateVersionSummary(
                **without_document(record(content_hash=None))
            )
        with pytest.raises(ValidationError, match="both or neither"):
            PlaybookTemplateVersionSummary(
                **without_document(record(base_version="0.3"))
            )
