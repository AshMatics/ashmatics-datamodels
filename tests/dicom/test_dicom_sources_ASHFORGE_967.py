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

"""Named DICOM sources and typed results (0.27.0, ASHFORGE-967, watch ADR-009).

Fixtures are the ADR-009 dev reference set: ORTHDEVAOG (Orthanc, DIMSE) and the dev
AHDS DICOM service (DICOMweb only, OAuth 2.0).
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.dicom import (
    DEMOGRAPHIC_FIELD_PURPOSE,
    DicomMoveResult,
    DicomPatientDemographics,
    DicomSeriesRow,
    DicomSourceDescriptor,
    DicomSourceEndpoint,
    DicomSourceHealth,
    DicomStudyRow,
    SiteDicomSource,
    validate_ae_title,
)

STUDY = "1.2.826.0.1.3680043.8.498.1"
SERIES = "1.2.826.0.1.3680043.8.498.1.1"
T0 = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)


def orthanc(**over) -> dict:
    d = {
        "name": "ORTHDEVAOG",
        "kind": "pacs",
        "status": "registered",
        "modes": ["exploratory", "governed"],
        "operations": ["echo", "query", "move_to_cube"],
        "dimse": {
            "called_ae_title": "ORTHDEVAOG",
            "calling_ae_title": "ASHCONN_ORTH",
            "move_destinations": ["ChRIS"],
        },
    }
    d.update(over)
    return d


def ahds(**over) -> dict:
    d = {
        "name": "ahds-dev",
        "kind": "cloud_archive",
        "status": "registered",
        "modes": ["exploratory"],
        "operations": ["echo", "query", "retrieve", "move_to_cube"],
        "auth_method": "oauth2_client_credentials",
        "dicomweb": {"qido_rs": True, "wado_rs": True},
    }
    d.update(over)
    return d


class TestDescriptor:
    def test_reference_sources_validate(self):
        o = DicomSourceDescriptor(**orthanc())
        a = DicomSourceDescriptor(**ahds())
        assert o.allows("move_to_cube") and o.usable_in("governed")
        assert a.dimse is None and not a.usable_in("governed")

    def test_descriptor_has_no_address_or_secret_fields(self):
        fields = set(DicomSourceDescriptor.model_fields)
        for banned in ("host", "port", "url", "secret", "password", "secret_ref"):
            assert not any(banned in f for f in fields), banned
        with pytest.raises(ValidationError):
            DicomSourceDescriptor(**orthanc(host="10.0.0.1"))

    def test_needs_a_protocol(self):
        with pytest.raises(ValidationError, match="DIMSE, DICOMweb"):
            DicomSourceDescriptor(**orthanc(dimse=None))

    def test_draft_is_exploratory_only(self):
        DicomSourceDescriptor(**orthanc(status="draft", modes=["exploratory"]))
        with pytest.raises(ValidationError, match="decision 4"):
            DicomSourceDescriptor(**orthanc(status="draft"))

    def test_move_to_cube_needs_a_destination_or_wado(self):
        d = orthanc()
        d["dimse"] = {**d["dimse"], "move_destinations": []}
        with pytest.raises(ValidationError, match="move_to_cube"):
            DicomSourceDescriptor(**d)
        with pytest.raises(ValidationError, match="move_to_cube"):
            DicomSourceDescriptor(
                **ahds(operations=["query", "move_to_cube"], dicomweb={"qido_rs": True})
            )

    def test_store_needs_stow_on_dicomweb_only_source(self):
        with pytest.raises(ValidationError, match="store"):
            DicomSourceDescriptor(**ahds(operations=["store"]))

    def test_oauth_on_dimse_only_is_refused(self):
        with pytest.raises(ValidationError, match="DICOMweb only"):
            DicomSourceDescriptor(**orthanc(auth_method="oauth2_client_credentials"))

    def test_duplicates_refused(self):
        with pytest.raises(ValidationError):
            DicomSourceDescriptor(**orthanc(operations=["echo", "echo"]))

    def test_calling_ae_is_not_the_destination(self):
        d = orthanc()
        d["dimse"] = {**d["dimse"], "calling_ae_title": "ChRIS"}
        with pytest.raises(ValidationError, match="item 13"):
            DicomSourceDescriptor(**d)

    def test_json_round_trip(self):
        o = DicomSourceDescriptor(**orthanc())
        assert DicomSourceDescriptor.model_validate_json(o.model_dump_json()) == o


class TestAETitle:
    @pytest.mark.parametrize("bad", ["", "    ", "A" * 17, "BAD\\AE", "TAB\tAE", "ÄE"])
    def test_refused(self, bad):
        with pytest.raises(ValueError):
            validate_ae_title(bad)

    def test_spaces_stripped_case_kept(self):
        assert validate_ae_title("  ChRIS ") == "ChRIS"


class TestSiteSource:
    def test_orthanc_site_record(self):
        s = SiteDicomSource(
            descriptor=orthanc(),
            endpoint={
                "source_name": "ORTHDEVAOG",
                "dimse_host": "orthanc",
                "dimse_port": 4242,
            },
            health={"probed_at": T0, "probe": "c_echo", "ok": True, "status_code": 0},
        )
        assert s.name == "ORTHDEVAOG"

    def test_endpoint_must_name_the_source(self):
        with pytest.raises(ValidationError, match="different source"):
            SiteDicomSource(
                descriptor=orthanc(),
                endpoint={"source_name": "other", "dimse_host": "h", "dimse_port": 1},
            )

    def test_dimse_needs_address(self):
        with pytest.raises(ValidationError, match="host and port"):
            SiteDicomSource(
                descriptor=orthanc(), endpoint={"source_name": "ORTHDEVAOG"}
            )

    def test_host_and_port_together(self):
        with pytest.raises(ValidationError):
            DicomSourceEndpoint(source_name="x", dimse_host="h")

    def test_oauth_needs_secret_ref(self):
        ep = {
            "source_name": "ahds-dev",
            "dicomweb_base_url": "https://x.dicom.azurehealthcareapis.com/v2",
        }
        with pytest.raises(ValidationError, match="secret reference"):
            SiteDicomSource(descriptor=ahds(), endpoint=ep)
        SiteDicomSource(
            descriptor=ahds(), endpoint={**ep, "secret_ref": "kv:ahds-dev-client"}
        )

    def test_none_takes_no_secret(self):
        with pytest.raises(ValidationError, match="no secret"):
            SiteDicomSource(
                descriptor=orthanc(),
                endpoint={
                    "source_name": "ORTHDEVAOG",
                    "dimse_host": "h",
                    "dimse_port": 4242,
                    "secret_ref": "kv:x",
                },
            )

    def test_tls_without_client_cert_is_allowed(self):
        SiteDicomSource(
            descriptor=orthanc(auth_method="tls"),
            endpoint={
                "source_name": "ORTHDEVAOG",
                "dimse_host": "h",
                "dimse_port": 2762,
            },
        )

    def test_tls_dicomweb_needs_https(self):
        with pytest.raises(ValidationError, match="https"):
            SiteDicomSource(
                descriptor=ahds(auth_method="tls"),
                endpoint={
                    "source_name": "ahds-dev",
                    "dicomweb_base_url": "http://x/v2",
                },
            )

    def test_health_detail_bounded(self):
        with pytest.raises(ValidationError):
            DicomSourceHealth(probed_at=T0, probe="qido", ok=False, detail="x" * 501)


class TestResults:
    def test_study_row(self):
        r = DicomStudyRow(
            source_name="ORTHDEVAOG",
            study_instance_uid=STUDY,
            study_date=date(2026, 1, 2),
            modalities_in_study=["CT", "SR"],
            demographics={
                "patient_sex": "F",
                "patient_age": "054Y",
                "postal_code": "021",
            },
        )
        assert r.modalities_in_study == ["CT", "SR"]
        assert not r.demographics.is_empty()

    @pytest.mark.parametrize("uid", ["1.2.abc", "1..2", "١.٢", "1." + "2" * 70])
    def test_bad_uid(self, uid):
        with pytest.raises(ValidationError):
            DicomSeriesRow(
                source_name="s", study_instance_uid=STUDY, series_instance_uid=uid
            )

    def test_no_phone_or_address_fields(self):
        fields = set(DicomPatientDemographics.model_fields)
        assert "patient_address" not in fields
        assert not any("telephone" in f or "phone" in f for f in fields)

    def test_every_demographic_has_a_purpose(self):
        assert set(DEMOGRAPHIC_FIELD_PURPOSE) == set(
            DicomPatientDemographics.model_fields
        )
        assert (
            DEMOGRAPHIC_FIELD_PURPOSE["country_of_residence"][0] == "CountryOfResidence"
        )

    def test_age_format(self):
        with pytest.raises(ValidationError):
            DicomPatientDemographics(patient_age="54")


def move(**over) -> dict:
    d = {
        "source_name": "ORTHDEVAOG",
        "destination_ae_title": "ChRIS",
        "level": "STUDY",
        "study_instance_uid": STUDY,
        "outcome": "success",
        "status_code": 0,
        "completed": 12,
        "started_at": T0,
        "finished_at": T0 + timedelta(seconds=4),
    }
    d.update(over)
    return d


class TestMoveResult:
    def test_success(self):
        assert DicomMoveResult(**move()).in_destination

    def test_partial_needs_failures(self):
        with pytest.raises(ValidationError, match="partial"):
            DicomMoveResult(**move(outcome="partial", status_code=0xB000))
        r = DicomMoveResult(**move(outcome="partial", status_code=0xB000, failed=1))
        assert r.in_destination

    def test_success_has_no_failures(self):
        with pytest.raises(ValidationError):
            DicomMoveResult(**move(failed=2))

    def test_series_level_names_series(self):
        with pytest.raises(ValidationError, match="names its series"):
            DicomMoveResult(**move(level="SERIES"))
        DicomMoveResult(**move(level="SERIES", series_instance_uids=[SERIES]))
        with pytest.raises(ValidationError, match="names no series"):
            DicomMoveResult(**move(series_instance_uids=[SERIES]))

    def test_level_is_study_or_series(self):
        with pytest.raises(ValidationError):
            DicomMoveResult(**move(level="IMAGE"))

    def test_times_in_order(self):
        with pytest.raises(ValidationError):
            DicomMoveResult(**move(finished_at=T0 - timedelta(seconds=1)))
