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
Typed DICOM query and move results (ASHFORGE-967; prototype REVIEW items 3, 4, 9, 15).

One shape for a study, series or instance row, so the watch Ninja API, coreapp and
the federated search (ADR-009 decision 6) share it. Values come back as the source
matched them: nothing here refilters.

Demographics are kept on purpose, for representative cohorts (REVIEW item 9). They are
optional and often empty, since a PACS answers C-FIND from its index. Each field's
purpose is in :data:`DEMOGRAPHIC_FIELD_PURPOSE`, the minimum-necessary justification a
consumer reads to decide where a field may be shown. These fields belong in cohort
balance views, never in logs or default list views.
"""

import re
from datetime import date, datetime

from pydantic import Field, field_validator, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .enums import DicomMoveOutcome, QueryRetrieveLevel
from .sources import DICOM_SOURCE_NAME_PATTERN, validate_ae_title

# [0-9], not \d: pydantic's regex engine reads \d as any Unicode digit.
DICOM_UID_PATTERN = r"^[0-9]+(\.[0-9]+)*$"
DICOM_UID_MAX_LENGTH = 64
POSTAL_CODE_PATTERN = r"^[A-Za-z0-9 -]{1,10}$"
PATIENT_AGE_PATTERN = r"^[0-9]{3}[DWMY]$"

_UID = Field(..., pattern=DICOM_UID_PATTERN, max_length=DICOM_UID_MAX_LENGTH)


DEMOGRAPHIC_FIELD_PURPOSE: dict[str, tuple[str, str]] = {
    # field: (DICOM keyword, why the package asks for it)
    "patient_birth_date": (
        "PatientBirthDate",
        "Age at study when PatientAge is empty; cohort age balance.",
    ),
    "patient_sex": ("PatientSex", "Cohort sex balance."),
    "patient_age": ("PatientAge", "Cohort age balance."),
    "patient_size": (
        "PatientSize",
        "Cohort body-size balance; dose-related subgroups.",
    ),
    "patient_weight": (
        "PatientWeight",
        "Cohort body-size balance; dose-related subgroups.",
    ),
    "ethnic_group": ("EthnicGroup", "Cohort ethnicity balance and bias analysis."),
    "country_of_residence": (
        "CountryOfResidence",
        "Cohort geography; site-mix analysis.",
    ),
    "region_of_residence": (
        "RegionOfResidence",
        "Cohort geography; site-mix analysis.",
    ),
    "postal_code": (
        "PatientAddress",
        "Cohort geography. Reduced from the address at ingest; the address is never "
        "stored. ZIP3 when the cohort must stay de-identifiable under Safe Harbor.",
    ),
}
"""Each demographic field, its DICOM source and its minimum-necessary purpose.

``PatientTelephoneNumbers`` is not requested: no cohort use. ``PatientReligiousPreference``
is not requested until a cohort use is named (REVIEW item 9).
"""


class DicomPatientDemographics(AshMaticsBaseModel):
    """Cohort demographics from a C-FIND answer or an instance header. All optional."""

    patient_birth_date: date | None = None
    patient_sex: str | None = Field(None, max_length=16)
    patient_age: str | None = Field(None, pattern=PATIENT_AGE_PATTERN)
    patient_size: float | None = Field(None, gt=0, description="Metres")
    patient_weight: float | None = Field(None, gt=0, description="Kilograms")
    ethnic_group: str | None = Field(None, max_length=64)
    country_of_residence: str | None = Field(None, max_length=64)
    region_of_residence: str | None = Field(None, max_length=64)
    postal_code: str | None = Field(
        None,
        pattern=POSTAL_CODE_PATTERN,
        description="Reduced from PatientAddress at ingest; never the address",
    )

    def is_empty(self) -> bool:
        return all(v is None for v in self.model_dump().values())


class DicomStudyRow(AshMaticsBaseModel):
    """One study, as one source answered for it."""

    source_name: str = Field(..., pattern=DICOM_SOURCE_NAME_PATTERN)
    study_instance_uid: str = _UID
    study_date: date | None = None
    study_time: str | None = Field(None, max_length=16)
    accession_number: str | None = Field(None, max_length=64)
    study_id: str | None = Field(None, max_length=64)
    study_description: str | None = Field(None, max_length=256)
    modalities_in_study: list[str] = Field(default_factory=list)
    number_of_study_related_series: int | None = Field(None, ge=0)
    number_of_study_related_instances: int | None = Field(None, ge=0)
    patient_id: str | None = Field(None, max_length=64)
    patient_name: str | None = Field(None, max_length=324)
    demographics: DicomPatientDemographics | None = None


class DicomSeriesRow(AshMaticsBaseModel):
    """One series, as one source answered for it."""

    source_name: str = Field(..., pattern=DICOM_SOURCE_NAME_PATTERN)
    study_instance_uid: str = _UID
    series_instance_uid: str = _UID
    series_number: int | None = None
    modality: str | None = Field(None, max_length=16)
    series_description: str | None = Field(None, max_length=256)
    body_part_examined: str | None = Field(None, max_length=64)
    series_date: date | None = None
    number_of_series_related_instances: int | None = Field(None, ge=0)


class DicomInstanceRow(AshMaticsBaseModel):
    """One instance (IMAGE level), as one source answered for it."""

    source_name: str = Field(..., pattern=DICOM_SOURCE_NAME_PATTERN)
    study_instance_uid: str = _UID
    series_instance_uid: str = _UID
    sop_instance_uid: str = _UID
    sop_class_uid: str | None = Field(
        None, pattern=DICOM_UID_PATTERN, max_length=DICOM_UID_MAX_LENGTH
    )
    instance_number: int | None = None


class DicomMoveResult(AshMaticsBaseModel):
    """How one C-MOVE ended (REVIEW items 3 and 4).

    The counts are the source's own final numbers, taken from its last response, never
    summed across pending responses. ``partial`` (B000) means some sub-operations
    failed and the rest are in the destination.
    """

    source_name: str = Field(..., pattern=DICOM_SOURCE_NAME_PATTERN)
    destination_ae_title: str
    level: QueryRetrieveLevel
    study_instance_uid: str = _UID
    series_instance_uids: list[str] = Field(default_factory=list)
    outcome: DicomMoveOutcome
    status_code: int | None = Field(None, ge=0, le=0xFFFF)
    completed: int = Field(0, ge=0)
    failed: int = Field(0, ge=0)
    warning: int = Field(0, ge=0)
    remaining: int | None = Field(None, ge=0)
    failed_sop_instance_uids: list[str] = Field(default_factory=list)
    error_comment: str | None = Field(None, max_length=500)
    started_at: datetime
    finished_at: datetime

    @field_validator("destination_ae_title")
    @classmethod
    def _ae(cls, value: str) -> str:
        return validate_ae_title(value)

    @field_validator("series_instance_uids", "failed_sop_instance_uids")
    @classmethod
    def _uids(cls, value: list[str]) -> list[str]:
        for uid in value:
            if len(uid) > DICOM_UID_MAX_LENGTH or not re.match(DICOM_UID_PATTERN, uid):
                raise ValueError(f"not a DICOM UID: {uid!r}")
        return value

    @model_validator(mode="after")
    def _rules(self) -> "DicomMoveResult":
        if self.level not in (
            QueryRetrieveLevel.STUDY.value,
            QueryRetrieveLevel.SERIES.value,
        ):
            raise ValueError("a move is at STUDY or SERIES level")
        if (
            self.level == QueryRetrieveLevel.SERIES.value
            and not self.series_instance_uids
        ):
            raise ValueError("a SERIES-level move names its series")
        if self.level == QueryRetrieveLevel.STUDY.value and self.series_instance_uids:
            raise ValueError("a STUDY-level move names no series")
        if self.outcome == DicomMoveOutcome.PARTIAL.value and self.failed == 0:
            raise ValueError("a partial move has at least one failed sub-operation")
        if self.outcome == DicomMoveOutcome.SUCCESS.value and self.failed != 0:
            raise ValueError("a successful move has no failed sub-operations")
        if self.finished_at < self.started_at:
            raise ValueError("a move finishes after it starts")
        return self

    @property
    def in_destination(self) -> bool:
        """Whether at least part of the move reached the destination."""
        return self.completed + self.warning > 0
