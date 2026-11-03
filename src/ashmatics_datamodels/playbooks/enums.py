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
Playbook template lifecycle status (ASHFORGE-851, coreapp ADR-070 D2).
"""

from enum import Enum


class PlaybookTemplateStatus(str, Enum):
    """Where one template version is in its life.

    A draft may change. A published version never changes; a fix is a new version.
    A retired version stays readable and is hidden from new setups.
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"
