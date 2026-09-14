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
Common base models and utilities shared across all jurisdictions.
"""

from ashmatics_datamodels.common.base import (
    AshMaticsBaseModel,
    AuditedModel,
    TimestampedModel,
)
from ashmatics_datamodels.common.enums import (
    ActionAuthority,
    AuthorizationStatus,
    ParsingStatus,
    Region,
    RegulatoryStatus,
    RiskCategory,
    SignalAccess,
)
from ashmatics_datamodels.common.frameworks import (
    RegulatoryFrameworkBase,
    RegulatoryFrameworkCreate,
    RegulatoryFrameworkResponse,
    RegulatoryFrameworkStats,
    RegulatoryFrameworkSummary,
    RegulatoryFrameworkUpdate,
)
from ashmatics_datamodels.common.regulators import (
    RegulatorBase,
    RegulatorCreate,
    RegulatorResponse,
    RegulatorStats,
    RegulatorSummary,
    RegulatorUpdate,
)
from ashmatics_datamodels.common.validators import (
    validate_country_code,
    validate_iso_date,
)

__all__ = [
    # Base models
    "AshMaticsBaseModel",
    "TimestampedModel",
    "AuditedModel",
    # Enums
    "AuthorizationStatus",
    "RegulatoryStatus",
    "ActionAuthority",
    "RiskCategory",
    "SignalAccess",
    "ParsingStatus",
    "Region",
    # Validators
    "validate_country_code",
    "validate_iso_date",
    # Regulators
    "RegulatorBase",
    "RegulatorCreate",
    "RegulatorUpdate",
    "RegulatorResponse",
    "RegulatorSummary",
    "RegulatorStats",
    # Regulatory Frameworks
    "RegulatoryFrameworkBase",
    "RegulatoryFrameworkCreate",
    "RegulatoryFrameworkUpdate",
    "RegulatoryFrameworkResponse",
    "RegulatoryFrameworkSummary",
    "RegulatoryFrameworkStats",
]
