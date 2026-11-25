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
Named DICOM sources and typed DICOM results (ASHFORGE-967, forge/watch ADR-009).

Shared by coreapp (the AI Registry's deployment data), the watch Django Ninja backend
and the Distributed DICOM connector. Pydantic models only.

Usage::

    from ashmatics_datamodels.dicom import (
        DicomSourceDescriptor,   # logical, what FORGE holds
        DicomSourceEndpoint,     # site part: addresses and secret reference
        SiteDicomSource,         # the two joined, with health
        DicomStudyRow, DicomSeriesRow, DicomInstanceRow, DicomMoveResult,
    )
"""

from .enums import (
    DicomAuthMethod,
    DicomMoveOutcome,
    DicomOperation,
    DicomProbeKind,
    DicomSourceKind,
    DicomSourceMode,
    DicomSourceStatus,
    QueryRetrieveLevel,
)
from .results import (
    DEMOGRAPHIC_FIELD_PURPOSE,
    DICOM_UID_MAX_LENGTH,
    DICOM_UID_PATTERN,
    DicomInstanceRow,
    DicomMoveResult,
    DicomPatientDemographics,
    DicomSeriesRow,
    DicomStudyRow,
)
from .sources import (
    AE_TITLE_MAX_LENGTH,
    DICOM_SOURCE_NAME_PATTERN,
    DicomSourceDescriptor,
    DicomSourceEndpoint,
    DicomSourceHealth,
    DicomWebProtocol,
    DimseProtocol,
    SiteDicomSource,
    validate_ae_title,
)

__all__ = [
    "AE_TITLE_MAX_LENGTH",
    "DEMOGRAPHIC_FIELD_PURPOSE",
    "DICOM_SOURCE_NAME_PATTERN",
    "DICOM_UID_MAX_LENGTH",
    "DICOM_UID_PATTERN",
    "DicomAuthMethod",
    "DicomInstanceRow",
    "DicomMoveOutcome",
    "DicomMoveResult",
    "DicomOperation",
    "DicomPatientDemographics",
    "DicomProbeKind",
    "DicomSeriesRow",
    "DicomSourceDescriptor",
    "DicomSourceEndpoint",
    "DicomSourceHealth",
    "DicomSourceKind",
    "DicomSourceMode",
    "DicomSourceStatus",
    "DicomStudyRow",
    "DicomWebProtocol",
    "DimseProtocol",
    "QueryRetrieveLevel",
    "SiteDicomSource",
    "validate_ae_title",
]
