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
Playbook template records (ASHFORGE-851, coreapp ADR-070 D2).

The record shape the KB stores and FORGE reads. Pydantic models only: the interior
grammar and its validator are ``ashmatics-playbook-grammar``'s.

Usage::

    from ashmatics_datamodels.playbooks import (
        PlaybookTemplateFacets,
        PlaybookTemplateStatus,
        PlaybookTemplateVersionRecord,
        PlaybookTemplateVersionSummary,
    )
"""

from .enums import PlaybookTemplateStatus
from .templates import (
    PLAYBOOK_CHANGE_NOTE_MAX_LENGTH,
    PLAYBOOK_CONTENT_HASH_PATTERN,
    PLAYBOOK_SLUG_PATTERN,
    PLAYBOOK_VERSION_MAX_LENGTH,
    PLAYBOOK_VERSION_PATTERN,
    REQUIRED_DOCUMENT_KEYS,
    PlaybookTemplateFacets,
    PlaybookTemplateVersionRecord,
    PlaybookTemplateVersionSummary,
)

__all__ = [
    "PLAYBOOK_CHANGE_NOTE_MAX_LENGTH",
    "PLAYBOOK_CONTENT_HASH_PATTERN",
    "PLAYBOOK_SLUG_PATTERN",
    "PLAYBOOK_VERSION_MAX_LENGTH",
    "PLAYBOOK_VERSION_PATTERN",
    "REQUIRED_DOCUMENT_KEYS",
    "PlaybookTemplateFacets",
    "PlaybookTemplateStatus",
    "PlaybookTemplateVersionRecord",
    "PlaybookTemplateVersionSummary",
]
