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
Named DICOM sources (ASHFORGE-967, forge/watch ADR-009 decisions 1 to 4).

A source is split in two on purpose, along the line ADR-009 decision 3 draws:

- :class:`DicomSourceDescriptor` is the logical record: name, kind, status, modes,
  operations, auth method, AE titles and protocol capabilities. It holds no network
  address and no secret reference, so it is what FORGE authors and sends to a site.
- :class:`DicomSourceEndpoint` is the site's part: host, port, base URL and the name
  of the secret in the site's secret store. It never leaves the site.

:class:`SiteDicomSource` joins the two with the source's last probe
(:class:`DicomSourceHealth`) and checks that they agree. It is what the watch
backend and the DICOM connector are built from.

If a contract later has FORGE hold addresses too (ADR-009 open question 1), FORGE
stores an endpoint beside the descriptor; neither model changes.

No secret value has a field anywhere in this module.
"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .enums import (
    DicomAuthMethod,
    DicomOperation,
    DicomProbeKind,
    DicomSourceKind,
    DicomSourceMode,
    DicomSourceStatus,
    QueryRetrieveLevel,
)

DICOM_SOURCE_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
SECRET_REF_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._/:-]{0,255}$"
AE_TITLE_MAX_LENGTH = 16
DICOMWEB_URL_PATTERN = r"^https?://[^\s]+$"
HOST_PATTERN = r"^[A-Za-z0-9]([A-Za-z0-9.:-]{0,252}[A-Za-z0-9])?$"


def validate_ae_title(value: str) -> str:
    """Check a DICOM AE title (PS3.5 VR AE) and return it stripped.

    1 to 16 characters from the default repertoire, with no backslash and no control
    characters. Leading and trailing spaces are not significant, so they are stripped;
    an all-space title is refused. Case is kept: sites match AE titles as written.
    """
    if not isinstance(value, str):
        raise ValueError("an AE title is a string")
    stripped = value.strip(" ")
    if not stripped:
        raise ValueError("an AE title may not be blank")
    if len(stripped) > AE_TITLE_MAX_LENGTH:
        raise ValueError(f"an AE title is at most {AE_TITLE_MAX_LENGTH} characters")
    for ch in stripped:
        if ch == "\\" or ord(ch) < 0x20 or ord(ch) > 0x7E:
            raise ValueError("an AE title uses printable ASCII only, with no backslash")
    return stripped


class DimseProtocol(AshMaticsBaseModel):
    """What a source offers over DIMSE, and the AE titles the package uses with it."""

    called_ae_title: str = Field(..., description="The source's own AE title")
    calling_ae_title: str = Field(
        ...,
        description=(
            "The AE title the package calls this source as. One per source, so the "
            "source's allow-list and the audit trail name the package, never the move "
            "destination."
        ),
    )
    query_levels: list[QueryRetrieveLevel] = Field(
        default_factory=lambda: [
            QueryRetrieveLevel.STUDY,
            QueryRetrieveLevel.SERIES,
            QueryRetrieveLevel.IMAGE,
        ],
        description="Query/Retrieve levels the source answers C-FIND at",
    )
    move_destinations: list[str] = Field(
        default_factory=list,
        description=(
            "AE titles the source will C-MOVE to (Oxidicom's, at least, for "
            "move_to_cube). The source must also know each one's address."
        ),
    )

    @field_validator("called_ae_title", "calling_ae_title")
    @classmethod
    def _ae_title(cls, value: str) -> str:
        return validate_ae_title(value)

    @field_validator("move_destinations")
    @classmethod
    def _destinations(cls, value: list[str]) -> list[str]:
        titles = [validate_ae_title(v) for v in value]
        if len(set(titles)) != len(titles):
            raise ValueError("each move destination is listed once")
        return titles

    @field_validator("query_levels")
    @classmethod
    def _levels(cls, value: list[QueryRetrieveLevel]) -> list[QueryRetrieveLevel]:
        if len(set(value)) != len(value):
            raise ValueError("each query level is listed once")
        return value

    @model_validator(mode="after")
    def _calling_is_not_a_destination(self) -> "DimseProtocol":
        if self.calling_ae_title == self.called_ae_title:
            raise ValueError("the calling AE title must differ from the source's own")
        if self.calling_ae_title in self.move_destinations:
            raise ValueError(
                "the calling AE title may not be a move destination: the package "
                "calls as itself, never as Oxidicom (REVIEW item 13)"
            )
        return self


class DicomWebProtocol(AshMaticsBaseModel):
    """Which DICOMweb services a source offers. Its base URL is site configuration."""

    qido_rs: bool = False
    wado_rs: bool = False
    stow_rs: bool = False

    @model_validator(mode="after")
    def _at_least_one(self) -> "DicomWebProtocol":
        if not (self.qido_rs or self.wado_rs or self.stow_rs):
            raise ValueError("a DICOMweb protocol offers at least one service")
        return self


class DicomSourceDescriptor(AshMaticsBaseModel):
    """The logical record of a named DICOM source (ADR-009 decisions 1 and 3).

    What FORGE holds and sends to a site: no network address, no secret reference.
    The rules that hold whatever the deployment:

    - at least one protocol;
    - a draft is exploratory only (decision 4);
    - every allowed operation has a protocol that can carry it.
    """

    name: str = Field(..., pattern=DICOM_SOURCE_NAME_PATTERN)
    display_name: str | None = Field(None, max_length=200)
    kind: DicomSourceKind
    status: DicomSourceStatus
    modes: list[DicomSourceMode] = Field(..., min_length=1)
    operations: list[DicomOperation] = Field(..., min_length=1)
    auth_method: DicomAuthMethod = DicomAuthMethod.NONE
    dimse: DimseProtocol | None = None
    dicomweb: DicomWebProtocol | None = None

    @field_validator("modes", "operations")
    @classmethod
    def _unique(cls, value: list) -> list:
        if len(set(value)) != len(value):
            raise ValueError("each value is listed once")
        return value

    @model_validator(mode="after")
    def _rules(self) -> "DicomSourceDescriptor":
        if self.dimse is None and self.dicomweb is None:
            raise ValueError("a source offers DIMSE, DICOMweb or both")
        if self.status == DicomSourceStatus.DRAFT.value and self.modes != [
            DicomSourceMode.EXPLORATORY.value
        ]:
            raise ValueError(
                "a draft source is usable in exploratory mode only (ADR-009 decision 4)"
            )
        web = self.dicomweb
        for op in self.operations:
            if not self._can_carry(op, web):
                raise ValueError(f"no protocol on this source can carry {op!r}")
        if self.auth_method == DicomAuthMethod.OAUTH2_CLIENT_CREDENTIALS.value and (
            web is None
        ):
            raise ValueError("OAuth 2.0 client credentials apply to DICOMweb only")
        if self.auth_method == DicomAuthMethod.BASIC.value and web is None:
            raise ValueError("basic auth applies to DICOMweb only")
        return self

    def _can_carry(self, op: str, web: DicomWebProtocol | None) -> bool:
        dimse = self.dimse
        qido = web is not None and web.qido_rs
        wado = web is not None and web.wado_rs
        if op == DicomOperation.ECHO.value:
            return dimse is not None or qido
        if op == DicomOperation.QUERY.value:
            return (dimse is not None and bool(dimse.query_levels)) or qido
        if op == DicomOperation.RETRIEVE.value:
            return dimse is not None or wado
        if op == DicomOperation.MOVE_TO_CUBE.value:
            return (dimse is not None and bool(dimse.move_destinations)) or wado
        if op == DicomOperation.STORE.value:
            return dimse is not None or (web is not None and web.stow_rs)
        return False

    def allows(self, operation: DicomOperation | str) -> bool:
        """Whether ``operation`` is in this source's allowed list."""
        value = operation.value if isinstance(operation, DicomOperation) else operation
        return value in self.operations

    def usable_in(self, mode: DicomSourceMode | str) -> bool:
        """Whether this source may be used for work in ``mode``."""
        value = mode.value if isinstance(mode, DicomSourceMode) else mode
        return value in self.modes


class DicomSourceEndpoint(AshMaticsBaseModel):
    """The site's part of a source: where it is and which secret to use.

    Site configuration only. ``secret_ref`` is the name of an entry in the site's
    secret store (for ``tls``, the client key and certificate bundle; for ``basic``
    and ``oauth2_client_credentials``, the credentials), read at call time.
    """

    source_name: str = Field(..., pattern=DICOM_SOURCE_NAME_PATTERN)
    dimse_host: str | None = Field(None, pattern=HOST_PATTERN)
    dimse_port: int | None = Field(None, ge=1, le=65535)
    dicomweb_base_url: str | None = Field(None, pattern=DICOMWEB_URL_PATTERN)
    secret_ref: str | None = Field(None, pattern=SECRET_REF_PATTERN)
    tls_ca_ref: str | None = Field(
        None,
        pattern=SECRET_REF_PATTERN,
        description="Secret-store name of the CA bundle that verifies the source",
    )
    tls_server_name: str | None = Field(None, pattern=HOST_PATTERN)
    acse_timeout_s: float = Field(30.0, gt=0, le=600)
    dimse_timeout_s: float = Field(60.0, gt=0, le=3600)
    network_timeout_s: float = Field(60.0, gt=0, le=3600)
    move_timeout_s: float = Field(
        3600.0,
        gt=0,
        le=86400,
        description="Longest a whole C-MOVE may run before the connector cancels it",
    )

    @model_validator(mode="after")
    def _port_with_host(self) -> "DicomSourceEndpoint":
        if (self.dimse_host is None) != (self.dimse_port is None):
            raise ValueError("a DIMSE host and port come together")
        return self


class DicomSourceHealth(AshMaticsBaseModel):
    """The source's last connection test. ``detail`` carries no PHI."""

    probed_at: datetime
    probe: DicomProbeKind
    ok: bool
    status_code: int | None = Field(None, ge=0, le=0xFFFF)
    latency_ms: float | None = Field(None, ge=0)
    detail: str | None = Field(None, max_length=500)


class SiteDicomSource(AshMaticsBaseModel):
    """A source as a site runs it: descriptor, endpoint and last probe, checked together.

    - the endpoint names this source;
    - each protocol in the descriptor has its address in the endpoint;
    - ``basic`` and ``oauth2_client_credentials`` have a ``secret_ref``; ``none`` has
      none; ``tls`` has one only for mutual TLS (the client key and certificate);
    - ``tls`` over DICOMweb needs an ``https`` URL.
    """

    descriptor: DicomSourceDescriptor
    endpoint: DicomSourceEndpoint
    health: DicomSourceHealth | None = None

    @model_validator(mode="after")
    def _agree(self) -> "SiteDicomSource":
        d, e = self.descriptor, self.endpoint
        if e.source_name != d.name:
            raise ValueError("the endpoint names a different source")
        if d.dimse is not None and e.dimse_host is None:
            raise ValueError("a DIMSE source needs a host and port")
        if d.dicomweb is not None and e.dicomweb_base_url is None:
            raise ValueError("a DICOMweb source needs a base URL")
        if d.auth_method == DicomAuthMethod.NONE.value:
            if e.secret_ref is not None:
                raise ValueError("auth method none takes no secret reference")
        elif e.secret_ref is None and d.auth_method != DicomAuthMethod.TLS.value:
            raise ValueError(f"auth method {d.auth_method!r} needs a secret reference")
        if (
            d.auth_method == DicomAuthMethod.TLS.value
            and e.dicomweb_base_url is not None
            and not e.dicomweb_base_url.startswith("https://")
        ):
            raise ValueError("TLS over DICOMweb needs an https base URL")
        return self

    @property
    def name(self) -> str:
        return self.descriptor.name
