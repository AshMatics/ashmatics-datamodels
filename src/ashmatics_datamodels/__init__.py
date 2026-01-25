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
AshMatics Core DataModels

Canonical Pydantic data models for AshMatics healthcare applications.
Provides FDA vocabulary, regulatory schemas, clinical AI use case taxonomy,
and MongoDB document schemas with standardized three-tier structure.

Usage:
    from ashmatics_datamodels.fda import FDA_ManufacturerBase, FDA_510kClearance
    from ashmatics_datamodels.common import AshMaticsBaseModel
    from ashmatics_datamodels.use_cases import UseCaseCategoryBase
    from ashmatics_datamodels.documents import EvidenceDocument, RegulatoryDocument
"""

__version__ = "0.3.1"
__author__ = "Asher Informatics PBC"

from ashmatics_datamodels.common import AshMaticsBaseModel, TimestampedModel

__all__ = [
    "__version__",
    "AshMaticsBaseModel",
    "TimestampedModel",
]
