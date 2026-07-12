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
Artifact-plane contracts (aigov-framework ADR-006, ASHKBAPP-99).

The two layers of the base-content / tenant-instantiation persistence
strategy: KB base reference content (``BaseArtifact``, ``CompiledView``)
and coreapp tenant instantiations (``InstanceArtifact``, ``InstanceIndex``).
Ported from the aigov-framework's legacy models_pydantic file, which is now
a deprecation shim over this module.

Usage::

    from ashmatics_datamodels.artifacts import (
        BaseArtifact,
        CompiledView,
        InstanceArtifact,
        InstanceIndex,
    )
"""

from .base_content import BaseArtifact, CompiledView, PracticeView, ToolRef
from .instances import (
    DecisionRecord,
    ExportRecord,
    InstanceArtifact,
    InstanceIndex,
)

__all__ = [
    # KB base content
    "BaseArtifact",
    "CompiledView",
    "PracticeView",
    "ToolRef",
    # tenant instances
    "InstanceArtifact",
    "InstanceIndex",
    "DecisionRecord",
    "ExportRecord",
]
