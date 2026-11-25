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
DICOM source vocabularies (ASHFORGE-967, forge/watch ADR-009 decision 1).

Record-shape enums, not ontology concepts: nothing here is bound to a scheme.
"""

from enum import Enum


class DicomSourceKind(str, Enum):
    """What kind of store a source is (ADR-009 decision 1)."""

    PACS = "pacs"
    VNA = "vna"
    CLOUD_ARCHIVE = "cloud_archive"
    PACKAGE_STORE = "package_store"


class DicomAuthMethod(str, Enum):
    """How the package authenticates to a source. The secret itself is never here."""

    NONE = "none"
    TLS = "tls"
    BASIC = "basic"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"


class DicomOperation(str, Enum):
    """The operations a source allows (ADR-009 decision 1)."""

    ECHO = "echo"
    QUERY = "query"
    RETRIEVE = "retrieve"
    MOVE_TO_CUBE = "move_to_cube"
    STORE = "store"


class DicomSourceMode(str, Enum):
    """The kind of work a source may be used for (forge/watch ADR-005 Amendment 1)."""

    EXPLORATORY = "exploratory"
    GOVERNED = "governed"


class DicomSourceStatus(str, Enum):
    """Where a source's record came from (ADR-009 decisions 3 and 4).

    A draft was added in watch by a site source-admin, for exploratory work only, and
    is invisible to the Site Controller. A registered source was authored in FORGE and
    came back as connector configuration.
    """

    DRAFT = "draft"
    REGISTERED = "registered"


class QueryRetrieveLevel(str, Enum):
    """DICOM Query/Retrieve Level (0008,0052), as written on the wire."""

    PATIENT = "PATIENT"
    STUDY = "STUDY"
    SERIES = "SERIES"
    IMAGE = "IMAGE"


class DicomProbeKind(str, Enum):
    """The connection test behind a source's health fields."""

    C_ECHO = "c_echo"
    QIDO = "qido"


class DicomMoveOutcome(str, Enum):
    """How a C-MOVE (or a bridged retrieve and send) ended.

    ``partial`` is DICOM status B000: some sub-operations failed. It is not a plain
    failure, because the study is partly in CUBE.
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
