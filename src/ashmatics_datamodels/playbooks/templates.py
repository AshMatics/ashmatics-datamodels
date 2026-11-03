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
The record of one playbook template version (ASHFORGE-851, coreapp ADR-070 D2).

The Asher Graph (the KB) holds every template version; FORGE reads a published one
and keeps a pinned copy. These models are the record's shape and nothing more: the
interior grammar and its validator are ``ashmatics-playbook-grammar``'s, and so is
``content_hash``, which is never computed here.
"""

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, field_validator, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .enums import PlaybookTemplateStatus

# [0-9], not \d: pydantic's regex engine reads \d as any Unicode digit, and a KB orders
# versions by casting their parts to integers in SQL (design D7).
PLAYBOOK_SLUG_PATTERN = r"^PBT-[A-Z]+-[A-Z0-9]+-[0-9]+$"
PLAYBOOK_VERSION_PATTERN = r"^[0-9]+(\.[0-9]+)*$"
PLAYBOOK_CONTENT_HASH_PATTERN = r"^[0-9a-f]{64}$"
PLAYBOOK_VERSION_MAX_LENGTH = 20
PLAYBOOK_CHANGE_NOTE_MAX_LENGTH = 300

REQUIRED_DOCUMENT_KEYS = ("lanes", "nodes", "edges")


class PlaybookTemplateFacets(AshMaticsBaseModel):
    """The catalogue facets of a template (coreapp ``playbook_catalog.yaml``, ``templates:``).

    Every field is optional and other keys are kept, because the catalogue grows:
    ``produces``, ``needs``, ``exchanges``, ``signed_off`` and ``fan_out`` are such keys
    today. The catalogue's ``slug`` and ``design_status`` are not facets, nor is any key
    the record has as a field of its own (design D12).
    """

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    intent: str | None = None
    tier: str | None = None
    playbook_class: str | None = None
    phase: str | None = None
    cadence: str | None = None
    subject_type: str | None = None
    run_cardinality: str | None = None
    trigger: str | None = None
    process_domains: list[str] | None = None
    base_practices: list[str] | None = None
    capability_areas: list[int] | None = None


class _PlaybookTemplateVersionFields(AshMaticsBaseModel):
    """What the full record and its summary share, the state rules included.

    The summary does not inherit from the record, nor the record from the summary:
    pydantic returns an instance of a subclass as it is, so a record validated as a
    summary would keep its ``document``.

    The state rules run on every assignment too, so a draft is not published field by
    field in place: build a new record.
    """

    slug: str = Field(..., pattern=PLAYBOOK_SLUG_PATTERN)
    version: str = Field(
        ..., pattern=PLAYBOOK_VERSION_PATTERN, max_length=PLAYBOOK_VERSION_MAX_LENGTH
    )
    status: PlaybookTemplateStatus
    grammar_version: str
    content_hash: str | None = Field(None, pattern=PLAYBOOK_CONTENT_HASH_PATTERN)
    facets: PlaybookTemplateFacets
    char_version: str | None = None
    variant_of: str | None = Field(None, pattern=PLAYBOOK_SLUG_PATTERN)
    base_version: str | None = Field(
        None, pattern=PLAYBOOK_VERSION_PATTERN, max_length=PLAYBOOK_VERSION_MAX_LENGTH
    )
    published_at: datetime | None = None
    published_by: str | None = None
    change_note: str | None = Field(None, max_length=PLAYBOOK_CHANGE_NOTE_MAX_LENGTH)
    validated_with: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def _check_state(self) -> "_PlaybookTemplateVersionFields":
        if self.status == PlaybookTemplateStatus.DRAFT.value:
            if self.content_hash is not None:
                raise ValueError("a draft has no content_hash")
        elif self.content_hash is None or self.published_at is None:
            raise ValueError(
                f"a {self.status} version needs content_hash and published_at"
            )
        return self

    @model_validator(mode="after")
    def _check_base_link(self) -> "_PlaybookTemplateVersionFields":
        if (self.variant_of is None) != (self.base_version is None):
            raise ValueError("variant_of and base_version go together: both or neither")
        if self.variant_of == self.slug and self.base_version == self.version:
            raise ValueError("a version cannot be a variant of itself")
        return self


class PlaybookTemplateVersionRecord(_PlaybookTemplateVersionFields):
    """One version of a playbook template, with its interior document.

    Only ``lanes``, ``nodes`` and ``edges`` are required of the document, and any other
    key is kept: ``slot_kinds`` is absent from 2 of the 90 published in coreapp's
    interiors-v0.25.0. The document is held as given, keys included, because
    ``content_hash`` is a function of it.
    """

    # A bare dict: the base model's str_strip_whitespace would rewrite dict[str, Any]'s keys.
    document: dict[Any, Any]

    @field_validator("document")
    @classmethod
    def _check_document(cls, document: dict[Any, Any]) -> dict[Any, Any]:
        missing = [key for key in REQUIRED_DOCUMENT_KEYS if key not in document]
        if missing:
            raise ValueError(f"document lacks {', '.join(missing)}")
        return document


class PlaybookTemplateVersionSummary(_PlaybookTemplateVersionFields):
    """One version of a playbook template without its document, for lists."""
